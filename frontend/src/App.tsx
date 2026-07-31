import { FormEvent, useMemo, useState } from 'react'
import { Activity, ArrowRight, BookOpen, CheckCircle2, Clock3, Menu, Search, ShieldCheck, Sparkles, X } from 'lucide-react'

type Source = { filename?: string; source?: string; publication_year?: string | number; evidence_level?: string; excerpt?: string; score?: number }
type Answer = { query: string; answer: string; sources: Source[]; disclaimer: string; demo?: boolean }

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
const examples = ['Первая линия терапии артериальной гипертензии', 'Тактика при остром коронарном синдроме', 'Дифференциальная диагностика головной боли']

const demoAnswer = (query: string): Answer => ({
  query,
  demo: true,
  answer: `По запросу «${query}» MedBot AI сформирует структурированный ответ только на основе загруженных клинических рекомендаций.\n\nВ рабочем режиме здесь отображаются: краткий вывод, рекомендуемая тактика, уровень доказательности и ссылки на исходные фрагменты документов.`,
  sources: [
    { filename: 'Клинические рекомендации.pdf', source: 'Минздрав РФ', publication_year: 2024, evidence_level: 'A', excerpt: 'Релевантный фрагмент клинической рекомендации отображается здесь.', score: .94 },
    { filename: 'Протокол ведения пациента.pdf', source: 'База MedBot AI', publication_year: 2025, evidence_level: 'B', excerpt: 'Дополнительный источник для проверки ответа.', score: .87 },
  ],
  disclaimer: 'Информация предназначена для медицинских специалистов и не заменяет клиническое решение врача.',
})

export default function App() {
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState<Answer | null>(null)
  const [loading, setLoading] = useState(false)
  const [menu, setMenu] = useState(false)
  const [history, setHistory] = useState<string[]>([])
  const canSubmit = useMemo(() => query.trim().length >= 2 && !loading, [query, loading])

  async function submit(event?: FormEvent) {
    event?.preventDefault()
    const value = query.trim()
    if (value.length < 2) return
    setLoading(true)
    setHistory(prev => [value, ...prev.filter(item => item !== value)].slice(0, 5))
    try {
      const response = await fetch(`${API}/ask`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: value }) })
      if (!response.ok) throw new Error('API unavailable')
      setAnswer(await response.json())
    } catch {
      setAnswer(demoAnswer(value))
    } finally { setLoading(false) }
  }

  function choose(value: string) { setQuery(value); setTimeout(() => document.getElementById('workspace')?.scrollIntoView({ behavior: 'smooth' }), 50) }

  return <div className="app">
    <header className="header">
      <a className="brand" href="#top" aria-label="MedBot AI"><span className="brand-mark"><Activity size={20}/></span><span>MedBot <b>AI</b></span></a>
      <nav className={menu ? 'nav open' : 'nav'}>
        <a href="#product" onClick={()=>setMenu(false)}>Возможности</a><a href="#workflow" onClick={()=>setMenu(false)}>Как работает</a><a href="#security" onClick={()=>setMenu(false)}>Безопасность</a>
        <a className="nav-cta" href="#workspace" onClick={()=>setMenu(false)}>Открыть MVP</a>
      </nav>
      <button className="menu" onClick={()=>setMenu(!menu)} aria-label="Меню">{menu ? <X/> : <Menu/>}</button>
    </header>

    <main id="top">
      <section className="hero">
        <div className="hero-copy">
          <div className="eyebrow"><Sparkles size={15}/> AI для медицинских специалистов</div>
          <h1>Доказательная медицина. <em>Без лишнего поиска.</em></h1>
          <p>MedBot AI находит ответы в клинических рекомендациях, показывает источники и помогает врачу быстрее принимать обоснованные решения.</p>
          <div className="hero-actions"><a className="primary" href="#workspace">Попробовать MVP <ArrowRight size={18}/></a><a className="secondary" href="#workflow">Как это работает</a></div>
          <div className="trust"><span><CheckCircle2/> Ответы с источниками</span><span><ShieldCheck/> Данные под контролем</span></div>
        </div>
        <div className="evidence-card">
          <div className="card-top"><span className="status"><i/> RAG-система активна</span><span>MEDBOT / 01</span></div>
          <p className="prompt">Какая первая линия терапии артериальной гипертензии?</p>
          <div className="response"><span className="response-label">Ответ на основе 3 документов</span><p>Стартовая терапия определяется сердечно-сосудистым риском и уровнем АД. Предпочтение отдаётся рациональным комбинациям препаратов.</p></div>
          <div className="source-row"><span><BookOpen/> Клинические рекомендации</span><b>A</b></div>
          <div className="source-row"><span><BookOpen/> Протокол Минздрава</span><b>B</b></div>
        </div>
      </section>

      <section className="workspace section" id="workspace">
        <div className="section-kicker">Рабочий прототип</div><h2>Задайте клинический вопрос</h2><p className="section-lead">Система проверит базу знаний и вернёт ответ вместе с релевантными источниками.</p>
        <div className="workspace-grid">
          <div className="ask-panel">
            <form onSubmit={submit}><label htmlFor="question">Клинический вопрос</label><textarea id="question" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Например: тактика лечения пациента с артериальной гипертензией..." maxLength={1000}/><div className="form-bottom"><span>{query.length}/1000</span><button className="primary" disabled={!canSubmit}>{loading ? <><span className="spinner"/> Анализирую</> : <><Search size={18}/> Найти ответ</>}</button></div></form>
            <div className="examples"><span>Примеры запросов</span>{examples.map(item=><button key={item} onClick={()=>choose(item)}>{item}</button>)}</div>
            {history.length > 0 && <div className="history"><span><Clock3 size={15}/> Недавние</span>{history.map(item=><button key={item} onClick={()=>choose(item)}>{item}</button>)}</div>}
          </div>
          <div className={`answer-panel ${answer ? 'filled' : ''}`}>
            {!answer ? <div className="empty"><div><Activity/></div><h3>Ответ появится здесь</h3><p>Введите вопрос — MedBot AI найдёт контекст и покажет источники.</p></div> : <>
              <div className="answer-head"><span>Результат анализа</span>{answer.demo && <b>Демо-режим</b>}</div><h3>{answer.query}</h3>{answer.answer.split('\n').filter(Boolean).map((p,i)=><p key={i}>{p}</p>)}
              <h4>Источники</h4>{answer.sources.map((source,i)=><article className="source" key={i}><div><BookOpen/><span><b>{source.filename || source.source || `Источник ${i+1}`}</b><small>{source.source} · {source.publication_year || 'год не указан'}</small></span>{source.evidence_level && <strong>{source.evidence_level}</strong>}</div>{source.excerpt && <p>{source.excerpt}</p>}</article>)}
              <div className="disclaimer"><ShieldCheck/>{answer.disclaimer}</div>
            </>}
          </div>
        </div>
      </section>

      <section className="features section" id="product"><div className="section-kicker">Возможности</div><h2>От вопроса до проверяемого ответа</h2><div className="feature-grid">
        <article><span>01</span><Search/><h3>Умный поиск</h3><p>Семантический поиск понимает смысл запроса, а не только совпадение слов.</p></article>
        <article><span>02</span><BookOpen/><h3>RAG с источниками</h3><p>Каждый вывод связан с конкретными фрагментами медицинских документов.</p></article>
        <article><span>03</span><Activity/><h3>Оценка доказательности</h3><p>Уровень доказательности виден прямо рядом с рекомендацией.</p></article>
      </div></section>

      <section className="workflow section" id="workflow"><div><div className="section-kicker">Принцип работы</div><h2>Три шага. Один прозрачный результат.</h2></div><ol><li><b>01</b><span><strong>Сформулируйте вопрос</strong><small>На естественном медицинском языке</small></span></li><li><b>02</b><span><strong>Система найдёт контекст</strong><small>В индексированной базе рекомендаций</small></span></li><li><b>03</b><span><strong>Проверьте ответ</strong><small>По источникам и уровням доказательности</small></span></li></ol></section>

      <section className="security section" id="security"><div className="security-icon"><ShieldCheck/></div><div><div className="section-kicker">Безопасность</div><h2>Помощник врача, а не замена врачу</h2><p>MedBot AI предназначен для профессионального использования. Система не ставит диагноз самостоятельно, сообщает о недостатке данных и сохраняет проверяемую связь ответа с источниками.</p></div></section>
    </main>
    <footer><a className="brand" href="#top"><span className="brand-mark"><Activity size={18}/></span>MedBot <b>AI</b></a><p>Информационная система поддержки принятия врачебных решений.</p><span>© 2026 MedBot AI</span></footer>
  </div>
}
