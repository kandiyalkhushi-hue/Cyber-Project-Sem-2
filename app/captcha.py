import random
import string

def generate_text_captcha():
    letters = string.ascii_letters + string.digits
    captcha_text = ''.join(random.choices(letters, k=6))
    # For simplicity, we just return text captcha and answer as text itself
    return {"type": "text", "question": captcha_text, "answer": captcha_text, "image": None}

def generate_math_captcha():
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    op = random.choice(["+", "-"])
    question = f"{num1} {op} {num2} = ?"
    answer = str(num1 + num2) if op == "+" else str(num1 - num2)
    return {"type": "math", "question": question, "answer": answer, "image": None}

def generate_captcha():
    # Randomly choose text or math captcha
    captcha_func = random.choice([generate_text_captcha, generate_math_captcha])
    return captcha_func()
