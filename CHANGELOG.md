# Changelog

## 1.2.1 – 2026-11-12

### Nowe
- Własna ikona integracji (`custom_components/moya_promo/brand/`), widoczna w Ustawieniach → Urządzenia i usługi od Home Assistant 2026.3.
- Przykładowa automatyzacja WhatsApp w `examples/automation_whatsapp.yaml`.

## 1.2.0 – 2026-11-12

### Nowe
- **Zdarzenie `moya_promo_new_promotion`** wysyłane dokładnie raz dla każdej nowej promocji. Integracja trwale zapamiętuje, którą promocję już zgłosiła, więc zdarzenie nie przepada, gdy promocja pojawi się w trakcie restartu HA, i nie dubluje się po restarcie. Dane promocji (kwota, kod, dni, linki, baner) są w `trigger.event.data`.
- **Akcja `moya_promo.announce_current`** – ręcznie wysyła zdarzenie dla bieżącej promocji (z `test: true`), do testowania automatyzacji.

### Poprawki
- Powiadomienia oparte na zmianie encji gubiły promocję, która pojawiła się podczas przeładowania integracji. Zalecana automatyzacja w README korzysta teraz ze zdarzenia.
- Po aktualizacji z 1.1.0 bieżąca promocja zostanie zgłoszona jeden raz.

## 1.1.0 – 2026-11-10

### Nowe
- **Kalendarz promocji** (`calendar.*`): każda promocja jako wydarzenie całodniowe z kodem rabatowym, kwotą i linkami do artykułu, listy stacji i regulaminu w opisie.
- Trwała historia promocji: przy każdym sprawdzeniu integracja czyta wszystkie promocje z pierwszej strony aktualności i zapisuje je w HA, więc kalendarz rośnie z czasem i przetrwa restart.
- Usunięcie integracji kasuje zapisaną historię.

### Instalacja / aktualizacja
HACS → *MOYA Promocje* → **Aktualizuj** (lub dodaj repozytorium `https://github.com/woojtekk/ha_moya` jako niestandardowe, kategoria **Integracja**), potem restart HA.

## 1.0.0 – 2026-11-10

### Nowe
- Pierwsza wersja integracji śledzącej promocje na stronie [moyaexpress.pl/aktualnosci](https://moyaexpress.pl/aktualnosci).
- Czujniki binarne **Promocja** i **Promocja dziś**.
- Sensory: **Rabat** (gr/l), **Kod rabatowy**, **Dni promocji**, **Początek / Koniec promocji**, **Status promocji**, **Tytuł promocji**.
- **Baner promocji** jako encja obrazu.
- Konfiguracja z interfejsu, sprawdzanie co 1–24 h (domyślnie 4 h); tłumaczenia PL i EN.
