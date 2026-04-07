import json
import random
import os
from datasets import load_dataset
from tqdm import tqdm


def generate_wrong_answers(context, correct_answer, num_wrong=2):
    """Генерация неправильных ответов из контекста"""
    sentences = context.replace('?', '.').replace('!', '.').split('.')
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    candidates = []
    for s in sentences:
        if correct_answer.lower() not in s.lower() and len(s) > 15:
            candidates.append(s[:80])

    if len(candidates) < num_wrong:
        candidates.append("Информация не указана в тексте")
    if len(candidates) < num_wrong:
        candidates.append("Другой вариант ответа")

    random.shuffle(candidates)
    return candidates[:num_wrong]


def convert_squad_to_training_format(dataset, output_file="training_data.jsonl", max_samples=5000):
    """Конвертация SberQUAD в формат для обучения"""
    training_data = []

    print(f"Обработка {max_samples} примеров из SberQUAD...")

    for i, example in enumerate(tqdm(dataset)):
        if i >= max_samples:
            break

        if not example.get('answers') or not example['answers'].get('text'):
            continue

        context = example['context']
        question = example['question']
        correct_answer = example['answers']['text'][0]

        wrong_answers = generate_wrong_answers(context, correct_answer, num_wrong=2)

        answers = [
            {"text": correct_answer, "is_correct": True},
            {"text": wrong_answers[0], "is_correct": False},
            {"text": wrong_answers[1], "is_correct": False}
        ]
        random.shuffle(answers)

        item = {
            "instruction": "На основе текста создай вопрос с 3 вариантами ответов. Только один вариант правильный.",
            "input": context[:1500],
            "output": json.dumps({
                "question": question,
                "answers": answers
            }, ensure_ascii=False)
        }

        training_data.append(item)

        if len(training_data) % 1000 == 0:
            with open(output_file, 'w', encoding='utf-8') as f:
                for item in training_data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            print(f"Сохранено {len(training_data)} примеров")

    with open(output_file, 'w', encoding='utf-8') as f:
        for item in training_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"Создано {len(training_data)} тренировочных примеров")
    return training_data


def split_data(input_file="training_data.jsonl", train_ratio=0.9):
    """Разделение данных на train и validation"""
    if not os.path.exists(input_file):
        print(f"Файл {input_file} не найден!")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        data = [json.loads(line) for line in f]

    random.shuffle(data)
    split_idx = int(len(data) * train_ratio)

    train_data = data[:split_idx]
    val_data = data[split_idx:]

    with open("train.jsonl", 'w', encoding='utf-8') as f:
        for item in train_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    with open("val.jsonl", 'w', encoding='utf-8') as f:
        for item in val_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"Train: {len(train_data)}, Validation: {len(val_data)}")


if __name__ == "__main__":
    print("Загрузка SberQUAD...")
    dataset = load_dataset("sberquad", split="train")
    print(f"Загружено {len(dataset)} примеров")

    training_data = convert_squad_to_training_format(dataset, max_samples=5000)
    split_data()