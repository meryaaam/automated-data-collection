# constant.py

categories = [
    {
        "slug": "arrete",
        "name": {
            "fr": "Arrêté",
            "ar": "قرار"
        }
    },
    {
        "slug": "avis",
        "name": {
            "fr": "Avis",
            "ar": "رأي"
        }
    },
    {
        "slug": "decret",
        "name": {
            "fr": "Décret",
            "ar": "مرسوم"
        }
    },
    {
        "slug": "loi",
        "name": {
            "fr": "Loi",
            "ar": "قانون"
        }
    },
    {
        "slug": "decret-gouvernemental",
        "name": {
            "fr": "Décret gouvernemental",
            "ar": "مرسوم حكومي"
        }
    },
    {
        "slug": "decret-loi",
        "name": {
            "fr": "Décret-Loi",
            "ar": "مرسوم قانون"
        }
    },
    {
        "slug": "cassation-penal",
        "name": {
            "fr": "Cassation Pénale",
            "ar": "جزائي"
        }
    },
    {
        "slug": "cassation-procedure-civile",
        "name": {
            "fr": "Procédures Civiles",
            "ar": "اجراءات مدنية"
        }
    },
    {
        "slug": "cassation-procedure-penale",
        "name": {
            "fr": "Procédures Pénales",
            "ar": "اجراءات جزائية"
        }
    },
    {
        "slug": "cassation-decisions-reunies",
        "name": {
            "fr": "Décisions des Chambres Réunies",
            "ar": "قرارات الدوائر المجتمعة"
        }
    }
]

def get_category_object(category_name):
    """Retourne l'objet catégorie correspondant à un nom donné."""
    for cat in categories:
        if category_name in cat["name"].values():
            return cat
    return None  # Retourne None si la catégorie n'est pas trouvée
