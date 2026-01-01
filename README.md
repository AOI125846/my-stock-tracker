# my-stock-tracker

פרויקט לעקיבה אחרי מניות — ממשק וובי בעברית, מתוכנן לסוחר מקצועי אך שמרני לגבי שינוי רזולוציות גרפים.

מה כדאי לדעת לפני הרצה
1. העתק `.env.example` ל־`.env` ומלא את המשתנים:
   - `SECRET_KEY` — החלף לערך אקראי בסביבת פרודקשן.
   - `STOCK_API_KEY` — אפשר להשאיר ריק; בהיעדרו המערכת משתמשת בנתוני דמה.
2. התקנת דרישות והרצה:
   - pip install -r requirements.txt
   - export FLASK_APP=src.my_stock_tracker.app
   - export FLASK_ENV=development
   - flask run
   - פתח: http://127.0.0.1:5000

הרשאה ורישיון
- רישיון: MIT (קובץ LICENSE בקוד).
