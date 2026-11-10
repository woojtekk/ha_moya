# Changelog

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
