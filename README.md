<h1 align="center">🛍️ MeroBazar – Modern Django Marketplace</h1>

<p align="center">
  <b>An advanced e-commerce marketplace built with Django & PostgreSQL, inspired by HamroBazar, with added features like a Hybrid Recommendation System and Khalti payment gateway integration.</b>
</p>

---

## 🚀 Overview
**MeroBazar** is a fully-featured online marketplace where users can **buy and sell products** easily.  
It comes with a **clean, user-friendly interface**, a **secure custom user system**, and **powerful features** to make the buying/selling experience seamless.

---

## ✨ Key Features
- 📦 **Buy & Sell Products** – Simple product listing and purchase process.
- 🔍 **Advanced Filtering & Search** – Quickly find the right products.
- 📄 **Pagination** – Smooth browsing for large product catalogs.
- 👤 **Custom User Profiles** – Personalized profiles for buyers & sellers.
- 🛒 **Orders Management** – View, track, and manage past orders.
- 🔐 **Custom User Model** – Built for flexibility beyond Django’s default authentication.
- 🤝 **Hybrid Recommendation System**  
  - Collaborative Filtering – Based on similar users’ activity.
  - Content-Based Filtering – Based on product attributes & preferences.
- 💳 **Khalti Payment Gateway Integration** – Fully functional and ready for secure transactions.
- 📂 **Modular Django App Structure** – Easy to scale and maintain.

---

## 💳 Khalti Payment Integration
MeroBazar includes **Khalti API integration** for secure and instant online payments.  
This allows buyers to complete transactions seamlessly inside the platform.

**Payment Flow:**
1. User selects a product and proceeds to checkout.
2. Khalti payment popup is triggered.
3. Upon successful payment, the order status is updated automatically.

<p align="center">
  <img src="https://cdn.khalti.com/static/img/khalti_logo.png" width="120" alt="Khalti Logo"/>
</p>

---

## 🛠️ Tech Stack
| Layer         | Technology |
|---------------|------------|
| **Backend**   | Django (Python) |
| **Database**  | PostgreSQL |
| **Frontend**  | Django Templates, HTML, CSS, JavaScript |
| **Payment**   | Khalti API |
| **Recommendation Engine** | Hybrid (Collaborative + Content-Based) Filtering |

---

## 📂 Project Structure
merobazar/<br>
├── adminapp/ # Admin side functionality
<br>
├── products/ # Product related functionality
<br>
├── userapp/ # User side functionality
<br>
├── templates/ # HTML templates
<br>
└── Media/ # images for the system
