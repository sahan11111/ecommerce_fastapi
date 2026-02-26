# 🛒 E-Commerce Backend with FastAPI

Welcome to the **E-Commerce Backend**!  
Built using [FastAPI](https://fastapi.tiangolo.com/) — blazing fast, modern, and ready for scale.

---

<div align="center">
  <img src="https://user-images.githubusercontent.com/1135055236/fastapi_banner.jpg" width="600" alt="E-Commerce Backend with FastAPI">
</div>

---

## 🚀 Features

- **Lightning Fast**: Powered by FastAPI for excellent performance.
- **Modular Design**: Easily extend your store with new features.
- **JWT Authentication**: Secure user authentication and authorization flows.
- **Product & Inventory Management**: Robust product CRUD operations.
- **Order Processing**: Seamless ordering pipeline.
- **Easy Integration**: API-first, ready for frontend or mobile.
- **Auto-generated Docs**: Interactive API docs with Swagger UI.

---

## ✨ API Documentation

After running the server, check out the interactive API docs:

- [Swagger UI](http://localhost:8000/docs)
- [ReDoc](http://localhost:8000/redoc)

---

## 📦 Project Structure

```text
ecommerce_fastapi/
├── app/
│   ├── main.py
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   └── ...
├── requirements.txt
└── README.md
```

---

## 🛠️ Quick Start

1. **Clone the repository**

    ```bash
    git clone https://github.com/sahan11111/ecommerce_fastapi.git
    cd ecommerce_fastapi
    ```

2. **Create a virtual environment & install dependencies**

    ```bash
    python -m venv venv
    source venv/bin/activate   # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3. **Run the development server**

    ```bash
    uvicorn app.main:app --reload
    ```

4. **Explore the API!**

    Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

---

## 🍀 Tech Stack

- **[FastAPI](https://fastapi.tiangolo.com/)** — web framework
- **[SQLAlchemy](https://www.sqlalchemy.org/)** — ORM (Database Layer)
- **[Pydantic](https://docs.pydantic.dev/)** — Data validation
- **[JWT](https://jwt.io/)** — Authentication
- **[Uvicorn](https://www.uvicorn.org/)** — ASGI server

---

## 🧩 Contributing

Contributions are welcome!  
Please open an issue or pull request to discuss improvements or bug fixes.

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📬 Contact

Created with ❤️ by [@sahan11111](https://github.com/sahan11111)

Feel free to reach out via GitHub issues for any queries!

---

<div align="center">
  <img src="https://img.shields.io/badge/FastAPI-Backend-blue?logo=fastapi" alt="FastAPI Badge"/>
  <img src="https://img.shields.io/badge/Python-3.9%2B-green?logo=python" alt="Python Badge"/>
</div>
