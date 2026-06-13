import os
import requests
from dotenv import load_dotenv

load_dotenv()

HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
HUNTER_URL = "https://api.hunter.io/v2/domain-search"

MAX_CONTACTS_SHOWN = 10  # Listede gösterilecek maksimum kişi sayısı

DEPARTMENT_LABELS = {
    "executive": "Executive / C-Suite",
    "it": "IT / Engineering",
    "finance": "Finance",
    "management": "Management",
    "sales": "Sales",
    "legal": "Legal",
    "support": "Support",
    "hr": "HR",
    "marketing": "Marketing",
    "communication": "Communications / PR",
}


def fetch_contacts(domain: str) -> list:
    """Domain'deki tüm kişileri Hunter.io'dan çeker."""
    response = requests.get(HUNTER_URL, params={
        "domain": domain,
        "limit": 10,
        "api_key": HUNTER_API_KEY
    })
    data = response.json()

    if "errors" in data:
        errors = data["errors"]
        # Free plan pagination sınırı — yine de gelen veriyi kullan
        if any(e.get("id") == "pagination_error" for e in errors):
            return data.get("data", {}).get("emails", [])
        raise ValueError(f"Hunter.io hatası: {errors}")

    emails = data.get("data", {}).get("emails", [])
    return emails


def filter_contacts(contacts: list, department: str = None) -> list:
    if not department:
        return contacts
    return [c for c in contacts if c.get("department") == department]


def get_departments(contacts: list) -> list:
    """Kişi listesinden mevcut departmanları çıkarır."""
    seen = set()
    departments = []
    for c in contacts:
        dept = c.get("department")
        if dept and dept not in seen:
            seen.add(dept)
            departments.append(dept)
    return sorted(departments)


def select_contact(domain: str) -> dict | None:
    """
    Kullanıcıya departman ve kişi seçtiren interaktif akış.
    Seçilen kişiyi dict olarak döner.
    """
    print(f"\n[Hunter.io] '{domain}' sorgulanıyor...")
    contacts = fetch_contacts(domain)

    if not contacts:
        print("Bu domain için kişi bulunamadı.")
        return None

    print(f"{len(contacts)} kişi bulundu.\n")

    # Departman seçimi
    departments = get_departments(contacts)
    print("Departman seç (Enter ile hepsini gör):")
    print("  [0] Tüm departmanlar")
    for i, dept in enumerate(departments, 1):
        label = DEPARTMENT_LABELS.get(dept, dept.capitalize())
        print(f"  [{i}] {label}")

    dept_choice = input("\nSeçim: ").strip()

    selected_dept = None
    if dept_choice.isdigit() and int(dept_choice) > 0:
        idx = int(dept_choice) - 1
        if 0 <= idx < len(departments):
            selected_dept = departments[idx]

    filtered = filter_contacts(contacts, selected_dept)

    if not filtered:
        print("Bu departmanda kişi bulunamadı.")
        return None

    # Kişi listesi
    filtered = filtered[:MAX_CONTACTS_SHOWN]
    print(f"\n{len(filtered)} kişi listeleniyor:\n")
    print(f"  {'#':<4} {'Ad Soyad':<25} {'Pozisyon':<30} {'Seviye':<12} {'Email'}")
    print("  " + "-" * 90)

    for i, c in enumerate(filtered, 1):
        name = f"{c.get('first_name', '')} {c.get('last_name', '')}".strip() or "-"
        position = (c.get("position") or "-")[:28]
        seniority = c.get("seniority") or "-"
        email = c.get("value") or "-"
        print(f"  [{i:<3}] {name:<25} {position:<30} {seniority:<12} {email}")

    print()
    choice = input("Kişi seç (numara) veya Enter ile atla: ").strip()

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(filtered):
            selected = filtered[idx]
            name = f"{selected.get('first_name', '')} {selected.get('last_name', '')}".strip()
            print(f"\nSeçildi: {name} — {selected.get('value')}")
            return selected

    print("Kişi seçilmedi.")
    return None
