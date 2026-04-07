import torch
import json
import re
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


class TrainedQuestionGenerator:
    def __init__(self, base_model="Qwen/Qwen2.5-1.5B-Instruct", adapter_path="./qwen-questions-lora"):
        print("Загрузка обученной модели...")
        self.tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"

        self.model = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True
        )
        self.model = PeftModel.from_pretrained(self.model, adapter_path)
        self.model.eval()

    def format_prompt(self, text, num_questions=3):
        return f"""### Инструкция:
На основе текста создай {num_questions} вопроса. У каждого вопроса должно быть 3 варианта ответа, только один правильный.

### Текст:
{text[:1500]}

### Ответ (в формате JSON, массив из {num_questions} объектов):
"""

    def generate_questions(self, text, num_questions=3, temperature=0.7):
        prompt = self.format_prompt(text, num_questions)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=1024,  # больше токенов для 3 вопросов
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1,
            )

        full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = full_response.split("### Ответ:")[-1].strip()

        # ВЫВОДИМ СЫРОЙ ОТВЕТ
        print("\n" + "=" * 60)
        print("СЫРОЙ ОТВЕТ МОДЕЛИ (без парсинга):")
        print("=" * 60)
        print(response[:2000])  # первые 2000 символов
        print("=" * 60 + "\n")

        # Пытаемся найти массив JSON
        try:
            # Ищем [...]
            json_match = re.search(r'\[\s*\{.*\}\s*\]', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                if isinstance(data, list) and len(data) >= num_questions:
                    return data[:num_questions]
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON: {e}")

        return None


if __name__ == "__main__":
    generator = TrainedQuestionGenerator()

    test_text = """
    Париж — столица и крупнейший город Франции, расположенный на реке Сена. Население города составляет около 2,2 миллиона человек, а вместе с пригородами — более 12 миллионов, что делает его крупнейшей городской агломерацией Европейского союза.

Город был основан ещё в III веке до нашей эры кельтским племенем паризиев, от которых и получил своё название. В 52 году до н. э. он был завоёван римлянами и стал называться Лютеция. Современное название окончательно закрепилось за городом в IV веке.

Париж известен своими всемирно знаменитыми достопримечательностями. Эйфелева башня, построенная Гюставом Эйфелем к Всемирной выставке 1889 года, является самым узнаваемым символом не только города, но и всей Франции. Её высота составляет 330 метров, она весит более 10 000 тонн, а для её покраски требуется около 60 тонн краски каждые 7 лет.
    """

    result = generator.generate_questions(test_text, num_questions=3)
    if result:
        print("Результат парсинга (3 вопроса):")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Не удалось извлечь JSON из ответа модели")