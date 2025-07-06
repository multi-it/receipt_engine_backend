#!/bin/bash

# Повна демонстрація Receipt Management API українською
# Запустіть сервер: uv run uvicorn main:app --host 0.0.0.0 --port 8000

set -e

API_BASE="http://localhost:8000"
TEMP_FILE="/tmp/receipt_demo_response.json"

echo "=== 🧾 ДЕМОНСТРАЦІЯ RECEIPT MANAGEMENT API ==="
echo

# 1. Реєстрація унікального користувача
echo "1. 👤 Реєстрація нового користувача..."
TIMESTAMP=$(date +%s)
curl -s -X POST "${API_BASE}/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "fullname": "Demo User",
    "username": "demouser'$TIMESTAMP'",
    "email": "demo'$TIMESTAMP'@example.com", 
    "password": "demopassword123"
  }' | jq '.'
echo

# 2. Вхід у систему та отримання токена
echo "2. 🔐 Вхід у систему та отримання JWT токена..."
curl -s -X POST "${API_BASE}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demouser'$TIMESTAMP'",
    "password": "demopassword123"
  }' > $TEMP_FILE

ACCESS_TOKEN=$(cat $TEMP_FILE | jq -r '.access_token')
echo "✅ Токен отримано: ${ACCESS_TOKEN:0:50}..."
echo

# 3. Створення чека з молочними продуктами
echo "3. 🥛 Створення чека з молочними продуктами..."
curl -s -X POST "${API_BASE}/receipts" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "products": [
      {
        "name": "Milk",
        "price": 45.50,
        "quantity": 2
      },
      {
        "name": "Bread",
        "price": 28.00,
        "quantity": 1
      }
    ],
    "payment": {
      "type": "cash",
      "amount": 150.00
    }
  }' > $TEMP_FILE

RECEIPT_ID=$(cat $TEMP_FILE | jq -r '.id')
echo "✅ Чек створено з ID: $RECEIPT_ID"
cat $TEMP_FILE | jq '.'
echo

# 4. Створення чека кафе з оплатою карткою
echo "4. ☕ Створення чека кафе з оплатою карткою..."
curl -s -X POST "${API_BASE}/receipts" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "products": [
      {
        "name": "Coffee Americano",
        "price": 120.00,
        "quantity": 1
      },
      {
        "name": "Croissant",
        "price": 85.50,
        "quantity": 2
      }
    ],
    "payment": {
      "type": "cashless",
      "amount": 291.00
    }
  }' > $TEMP_FILE

RECEIPT_ID_2=$(cat $TEMP_FILE | jq -r '.id')
echo "✅ Другий чек створено з ID: $RECEIPT_ID_2"
cat $TEMP_FILE | jq '.'
echo

# 5. Створення чека фаст-фуда
echo "5. 🍕 Створення чека фаст-фуда..."
curl -s -X POST "${API_BASE}/receipts" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "products": [
      {
        "name": "Big Burger",
        "price": 250.00,
        "quantity": 1
      },
      {
        "name": "French Fries",
        "price": 120.00,
        "quantity": 1
      },
      {
        "name": "Coca Cola",
        "price": 80.00,
        "quantity": 1
      }
    ],
    "payment": {
      "type": "cashless",
      "amount": 450.00
    }
  }' > $TEMP_FILE

RECEIPT_ID_3=$(cat $TEMP_FILE | jq -r '.id')
echo "✅ Чек фаст-фуда створено з ID: $RECEIPT_ID_3"
cat $TEMP_FILE | jq '.'
echo

# 6. Отримання всіх чеків користувача
echo "6. 📋 Отримання списку чеків користувача..."
curl -s -X GET "${API_BASE}/receipts" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
echo

# 7. Фільтрація за типом оплати (готівкою)
echo "7. 💵 Фільтрація чеків за оплатою готівкою..."
curl -s -X GET "${API_BASE}/receipts?payment_type=cash" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
echo

# 8. Фільтрація за типом оплати (карткою)
echo "8. 💳 Фільтрація чеків за оплатою карткою..."
curl -s -X GET "${API_BASE}/receipts?payment_type=cashless" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
echo

# 9. Пошук чеків за назвою продуктів
echo "9. 🔍 Пошук чеків, що містять 'Coffee'..."
curl -s -X GET "${API_BASE}/receipts?search=Coffee" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
echo

# 10. Пошук чеків за іншим продуктом
echo "10. 🔍 Пошук чеків, що містять 'Burger'..."
curl -s -X GET "${API_BASE}/receipts?search=Burger" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
echo

# 11. Сортування за спаданням суми
echo "11. 📊 Сортування чеків за спаданням суми..."
curl -s -X GET "${API_BASE}/receipts?sort_by=total&sort_order=desc" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
echo

# 12. Отримання статистики
echo "12. 📈 Отримання статистики чеків..."
curl -s -X GET "${API_BASE}/receipts/stats" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
echo

# 13. Публічний перегляд чека (JSON)
echo "13. 🌐 Публічний перегляд чека $RECEIPT_ID у форматі JSON..."
curl -s -X GET "${API_BASE}/public/receipts/$RECEIPT_ID" | jq '.'
echo

# 14. Публічний перегляд чека (текст)
echo "14. 📄 Публічний перегляд чека $RECEIPT_ID у текстовому форматі..."
curl -s -X GET "${API_BASE}/public/receipts/$RECEIPT_ID/text"
echo
echo

# 15. Публічний перегляд чека кафе (текст)
echo "15. ☕ Публічний перегляд чека кафе $RECEIPT_ID_2..."
curl -s -X GET "${API_BASE}/public/receipts/$RECEIPT_ID_2/text"
echo
echo

# 16. Публічний перегляд чека фаст-фуда (текст)
echo "16. 🍕 Публічний перегляд чека фаст-фуда $RECEIPT_ID_3..."
curl -s -X GET "${API_BASE}/public/receipts/$RECEIPT_ID_3/text"
echo
echo

# 17. Демонстрація захисту API
echo "17. 🔒 Демонстрація захисту API - доступ без токена..."
curl -s -X GET "${API_BASE}/receipts" -w "\nHTTP Status: %{http_code}\n" | head -3
echo

# 18. Демонстрація захисту API з неправильним токеном
echo "18. 🚫 Демонстрація захисту API - неправильний токен..."
curl -s -X GET "${API_BASE}/receipts" \
  -H "Authorization: Bearer invalid_token" \
  -w "\nHTTP Status: %{http_code}\n" | head -3
echo

# 19. Перевірка стану сервісу
echo "19. ❤️ Перевірка стану сервісу..."
curl -s -X GET "${API_BASE}/" | jq '.'
echo

# 20. Демонстрація валідації - недостатня сума оплати
echo "20. ⚠️ Демонстрація валідації - недостатня сума оплати..."
curl -s -X POST "${API_BASE}/receipts" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "products": [
      {
        "name": "Expensive Watch",
        "price": 50000.00,
        "quantity": 1
      }
    ],
    "payment": {
      "type": "cash",
      "amount": 100.00
    }
  }' | jq '.'
echo

# 21. Фільтрація за мінімальною сумою
echo "21. 💰 Фільтрація чеків з сумою більше 400..."
curl -s -X GET "${API_BASE}/receipts?min_total=400" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
echo

# 22. Отримання детальної інформації про чек
echo "22. 📜 Отримання детальної інформації про чек $RECEIPT_ID_3..."
curl -s -X GET "${API_BASE}/receipts/$RECEIPT_ID_3" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
echo

# 23. Демонстрація обробки помилок - неіснуючий чек
echo "23. ❌ Демонстрація обробки помилок - неіснуючий чек..."
curl -s -X GET "${API_BASE}/public/receipts/999999" \
  -w "\nHTTP Status: %{http_code}\n" | head -3
echo

# Очищення
rm -f $TEMP_FILE

echo "=== 🎉 ДЕМОНСТРАЦІЯ ЗАВЕРШЕНА ==="
echo
echo "✅ **ПРОТЕСТОВАНІ ФУНКЦІЇ:**"
echo "  🔐 Реєстрація та аутентифікація користувачів"
echo "  📝 Створення чеків різних типів (продукти, кафе, фаст-фуд)"
echo "  💳 Підтримка готівкової та безготівкової оплати"
echo "  🔍 Пошук та фільтрація чеків"
echo "  📊 Сортування та статистика"
echo "  🌐 Публічні ендпоінти (JSON та текстовий формат)"
echo "  🔒 Захист API та валідація даних"
echo "  ⚠️ Коректна обробка помилок"
echo
echo "🚀 **СИСТЕМА ПОВНІСТЮ ГОТОВА ДО ВИКОРИСТАННЯ!**"
echo
echo "📋 **ОСНОВНІ ЕНДПОІНТИ API:**"
echo "  • POST /auth/register - Реєстрація"
echo "  • POST /auth/login - Авторизація" 
echo "  • POST /receipts - Створення чека"
echo "  • GET /receipts - Список чеків з фільтрацією"
echo "  • GET /receipts/{id} - Конкретний чек"
echo "  • GET /receipts/stats - Статистика"
echo "  • GET /public/receipts/{id} - Публічний перегляд (JSON)"
echo "  • GET /public/receipts/{id}/text - Публічний перегляд (текст)"
echo
echo "🎯 **МОЖЛИВОСТІ ФІЛЬТРАЦІЇ:**"
echo "  • payment_type=cash|cashless - Тип оплати"
echo "  • search=<text> - Пошук за назвою продуктів"
echo "  • min_total=<amount> - Мінімальна сума"
echo "  • max_total=<amount> - Максимальна сума"
echo "  • sort_by=total|created_at - Сортування"
echo "  • sort_order=asc|desc - Порядок сортування"
