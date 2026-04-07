import torch
import json
import os
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
from datasets import Dataset

# Конфигурация
MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
OUTPUT_DIR = "./qwen-questions-lora"
LORA_RANK = 8
LORA_ALPHA = 16
LORA_DROPOUT = 0.1
MAX_LENGTH = 512
BATCH_SIZE = 2
GRADIENT_ACCUMULATION = 4
EPOCHS = 3
LEARNING_RATE = 2e-4


def format_prompt(instruction, input_text):
    return f"### Инструкция:\n{instruction}\n\n### Текст:\n{input_text}\n\n### Ответ:\n"


def load_training_data(file_path="train.jsonl"):
    if not os.path.exists(file_path):
        print(f"Файл {file_path} не найден!")
        return None

    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                item = json.loads(line)
                prompt = format_prompt(item['instruction'], item['input'])
                response = item['output']
                # Добавляем специальный токен конца
                full_text = prompt + response + "<|im_end|>"
                data.append({"text": full_text})
            except json.JSONDecodeError:
                continue

    print(f"Загружено {len(data)} примеров")
    return Dataset.from_list(data)


def tokenize_function(examples, tokenizer):
    """Токенизация с правильными labels (маскируем prompt)"""
    texts = examples["text"]

    # Токенизируем весь текст
    tokenized = tokenizer(
        texts,
        truncation=True,
        max_length=MAX_LENGTH,
        padding="max_length",
        return_tensors=None
    )

    input_ids = tokenized["input_ids"]

    # Находим позицию, где начинается ответ
    # Ищем "### Ответ:\n" в токенах
    answer_start_token = tokenizer.encode("### Ответ:\n", add_special_tokens=False)
    labels = []

    for ids in input_ids:
        # Ищем позицию начала ответа
        start_pos = -1
        for i in range(len(ids) - len(answer_start_token) + 1):
            if ids[i:i + len(answer_start_token)] == answer_start_token:
                start_pos = i + len(answer_start_token)
                break

        # Создаем labels: -100 для всех токенов до ответа, остальные копируем
        label = [-100] * len(ids)
        if start_pos != -1:
            label[start_pos:] = ids[start_pos:]
        labels.append(label)

    tokenized["labels"] = labels
    return tokenized


def main():
    print("=" * 50)
    print("Загрузка модели Qwen 1.5B...")
    print("=" * 50)

    if not os.path.exists("train.jsonl"):
        print("Ошибка: train.jsonl не найден!")
        print("Сначала запустите prepare_squad_data.py")
        return

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # 4-bit квантизация
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        use_cache=False,
    )
    print("Модель загружена")

    model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        bias="none",
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print("\nЗагрузка тренировочных данных...")
    train_dataset = load_training_data("train.jsonl")
    val_dataset = load_training_data("val.jsonl")

    if train_dataset is None or len(train_dataset) == 0:
        print("Нет тренировочных данных!")
        return

    print("\nТокенизация данных...")
    train_dataset = train_dataset.map(
        lambda x: tokenize_function(x, tokenizer),
        batched=True,
        remove_columns=train_dataset.column_names
    )

    if val_dataset and len(val_dataset) > 0:
        val_dataset = val_dataset.map(
            lambda x: tokenize_function(x, tokenizer),
            batched=True,
            remove_columns=val_dataset.column_names
        )

    # Data collator для динамического padding
    from transformers import DataCollatorForSeq2Seq
    data_collator = DataCollatorForSeq2Seq(
        tokenizer,
        padding=True,
        return_tensors="pt"
    )

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        num_train_epochs=EPOCHS,
        learning_rate=LEARNING_RATE,
        fp16=True,
        save_steps=500,
        eval_steps=500,
        logging_steps=50,
        eval_strategy="steps",
        save_total_limit=2,
        load_best_model_at_end=True,
        report_to="none",
        push_to_hub=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset if val_dataset and len(val_dataset) > 0 else None,
        data_collator=data_collator,
    )

    print("\n" + "=" * 50)
    print("Начало обучения...")
    print("=" * 50)

    trainer.train()

    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"\nМодель сохранена в {OUTPUT_DIR}")


if __name__ == "__main__":
    main()