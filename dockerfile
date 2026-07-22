# Python 3.11 - pydantic-core kabi paketlar uchun tayyor (prebuilt) wheel
# mavjud, shuning uchun Rust/cargo orqali manbadan qurish shart bo'lmaydi.
FROM python:3.11-slim

# Konteyner ichidagi ishchi papka
WORKDIR /app

# Avval faqat requirements.txt'ni nusxalaymiz - shu orqali Docker
# kutubxonalar o'zgarmasa qayta yuklab olmaydi (build tezroq bo'ladi)
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Qolgan barcha loyiha fayllarini nusxalaymiz
COPY . .

# Botni ishga tushirish
CMD ["python", "-m", "app.main"]