---
title: Dashboard — Мониторинг базы знаний
type: dashboard
tags: [dashboard, мета]
created: 2026-07-28
---

# 📊 Dashboard — База медицинских знаний MedBot AI

> Автоматический мониторинг актуальности и полноты базы знаний

---

## ⚠️ Требуют обновления (протоколы старше 2 лет)

```dataview
TABLE 
  specialty as "Специальность",
  publication_year as "Год",
  source as "Источник",
  evidence_level as "Уровень"
FROM "01-Протоколы"
WHERE status = "active"
  AND publication_year < 2024
SORT publication_year ASC
LIMIT 20
```

> [!warning] Приоритет обновления
> Протоколы старше 2 лет могут содержать устаревшие рекомендации

---

## ✅ Актуальные протоколы (2024-2026)

```dataview
TABLE 
  specialty as "Специальность",
  publication_year as "Год",
  evidence_level as "Уровень"
FROM "01-Протоколы"
WHERE status = "active"
  AND publication_year >= 2024
SORT publication_year DESC
```

---

## 📈 Статистика по специальностям

```dataview
TABLE 
  rows.file.link as "Протоколы",
  length(rows) as "Количество"
FROM "01-Протоколы"
WHERE status = "active"
GROUP BY specialty
SORT length(rows) DESC
```

---

## 🔬 Распределение по уровням доказательности

```dataview
TABLE 
  length(rows) as "Количество",
  round(length(rows) * 100 / 17, 1) + "%" as "Процент"
FROM "01-Протоколы"
WHERE status = "active"
GROUP BY evidence_level
SORT evidence_level ASC
```

> [!info] Целевое распределение
> - Уровень A (мета-анализы, РКИ): >60%
> - Уровень B (контролируемые исследования): 20-30%
> - Уровень C и ниже: <20%

---

## 📚 Последние добавленные протоколы

```dataview
TABLE 
  specialty as "Специальность",
  publication_year as "Год",
  created as "Добавлен"
FROM "01-Протоколы"
WHERE status = "active"
SORT created DESC
LIMIT 10
```

---

## 🏥 Источники документов

```dataview
TABLE 
  length(rows) as "Количество протоколов"
FROM "01-Протоколы"
WHERE status = "active"
GROUP BY source
SORT length(rows) DESC
```

---

## 🔗 Связность базы знаний

### Топ-10 самых связанных документов

```dataview
TABLE 
  length(file.inlinks) as "Входящие ссылки",
  length(file.outlinks) as "Исходящие ссылки",
  length(file.inlinks) + length(file.outlinks) as "Всего связей"
FROM "01-Протоколы" OR "02-Симптомы" OR "03-Препараты" OR "04-Диагнозы"
SORT (length(file.inlinks) + length(file.outlinks)) DESC
LIMIT 10
```

> [!tip] Цель
> Каждый протокол должен иметь минимум 5-10 связей с другими документами

---

## 📋 Пустые или незавершенные разделы

### Симптомы без связей с заболеваниями

```dataview
LIST
FROM "02-Симптомы"
WHERE length(file.outlinks) < 2
```

### Препараты без протоколов применения

```dataview
LIST
FROM "03-Препараты"
WHERE length(file.outlinks) < 1
```

---

## 🎯 Целевые метрики качества

| Метрика | Текущее | Целевое | Статус |
|---------|---------|---------|--------|
| Протоколов (active) | `= length(filter(file.lists.file, (x) => contains(x.path, "01-Протоколы")))` | 100+ | 🟡 |
| Уровень A+B (%) | — | >80% | — |
| Средний возраст (лет) | — | <2 | — |
| Связей на документ | — | >5 | — |
| Покрытие специальностей | 5 | 15+ | 🟡 |

---

## 🔄 План обновлений

### Q3 2026
- [ ] Обновить протоколы кардиологии 2023 года
- [ ] Добавить 20 новых протоколов эндокринологии
- [ ] Создать карточки для 50 препаратов

### Q4 2026
- [ ] Полная ревизия неврологических протоколов
- [ ] Добавить раздел "Онкология"
- [ ] Интеграция с актуальными клиническими рекомендациями Минздрава

---

## 📝 Последнее обновление Dashboard

**Дата:** 2026-07-28  
**Ответственный:** MedBot AI Team

---

## 🔗 Навигация

- [[Источники]] — список источников данных
- [[Соглашения]] — правила оформления документов
- [[История обновлений]] — changelog базы знаний
