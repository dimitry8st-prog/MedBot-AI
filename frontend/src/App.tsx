const DOCS_URL = "http://127.0.0.1:8002/docs";
const GITHUB_URL = "https://github.com/dimitry8st-prog/MedBot-AI";

function ProductStage() {
  return (
    <div className="relative h-full min-h-[420px] w-full overflow-hidden bg-[radial-gradient(circle_at_20%_20%,#2a8f7f_0%,transparent_42%),radial-gradient(circle_at_80%_0%,#c9b8a0_0%,transparent_35%),linear-gradient(160deg,#123f3a_0%,#0f1c1a_55%,#1a2e2a_100%)]">
      <div className="hero-orb absolute -left-10 top-16 h-56 w-56 rounded-full bg-[#1f6f63]/35 blur-3xl" />
      <div className="absolute inset-0 opacity-30 [background-image:linear-gradient(rgba(255,255,255,0.06)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.06)_1px,transparent_1px)] [background-size:48px_48px]" />

      <div className="relative z-10 flex h-full flex-col justify-between p-6 text-foam sm:p-8 lg:p-10">
        <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.22em] text-white/55">
          <span>Клинический поиск</span>
          <span>Evidence A–E</span>
        </div>

        <div className="mx-auto w-full max-w-xl rounded-2xl border border-white/10 bg-black/25 p-5 shadow-soft backdrop-blur-md sm:p-6">
          <p className="text-[11px] uppercase tracking-[0.18em] text-[#C9B8A0]">Запрос врача</p>
          <p className="mt-3 font-display text-xl leading-snug text-white sm:text-2xl">
            Первая линия терапии артериальной гипертензии
            <span className="cursor-blink ml-1 inline-block h-5 w-[2px] translate-y-[3px] bg-[#C9B8A0] align-middle" />
          </p>

          <div className="mt-6 space-y-3 border-t border-white/10 pt-5 text-sm leading-relaxed text-white/80">
            <p>
              По клиническим рекомендациям Минздрава: иАПФ, БРА, антагонисты кальция,
              тиазидные диуретики.
            </p>
            <p className="text-white/55">
              Источник: TEST_cardiology_hypertension_2024 · уровень A · 2024
            </p>
          </div>
        </div>

        <p className="max-w-sm text-xs leading-relaxed text-white/45">
          Ответ строится только по найденному контексту RAG. Без замены очной консультации.
        </p>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <div className="bg-foam text-ink">
      <header className="absolute inset-x-0 top-0 z-20">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <a href="#top" className="font-display text-lg tracking-tight text-ink">
            MedBot AI
          </a>
          <nav className="hidden items-center gap-8 text-sm text-ink/70 sm:flex">
            <a href="#how" className="hover:text-ink">
              Как работает
            </a>
            <a href="#stack" className="hover:text-ink">
              Стек
            </a>
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noreferrer"
              className="hover:text-ink"
            >
              GitHub
            </a>
          </nav>
        </div>
      </header>

      <main id="top">
        <section className="relative min-h-[100svh] overflow-hidden">
          <div className="absolute inset-0 bg-[linear-gradient(120deg,#f4faf7_0%,#e7f0ec_48%,#d9ebe4_100%)]" />
          <div className="absolute -right-24 top-10 h-[520px] w-[520px] rounded-full bg-[#1f6f63]/10 blur-3xl" />

          <div className="relative mx-auto grid min-h-[100svh] max-w-6xl items-center gap-10 px-6 pb-16 pt-28 lg:grid-cols-[0.95fr_1.05fr] lg:gap-14 lg:pb-20 lg:pt-24">
            <div>
              <p className="animate-rise font-display text-5xl leading-none tracking-tight text-seaDeep sm:text-6xl lg:text-7xl">
                MedBot AI
              </p>
              <h1 className="animate-rise-delay mt-6 max-w-xl font-display text-3xl leading-tight text-ink sm:text-4xl">
                Клинические протоколы — за секунды, с уровнем доказательности
              </h1>
              <p className="animate-rise-late mt-5 max-w-md text-base leading-relaxed text-ink/70 sm:text-lg">
                RAG-поиск по рекомендациям и ответ GigaChat для врача. Не заменяет специалиста —
                ускоряет доступ к знаниям.
              </p>

              <div className="animate-rise-late mt-9 flex flex-wrap items-center gap-4">
                <a
                  href={DOCS_URL}
                  target="_blank"
                  rel="noreferrer"
                  className="bg-sea px-6 py-3 text-sm font-semibold text-white transition hover:bg-seaDeep"
                >
                  Открыть API
                </a>
                <a
                  href={GITHUB_URL}
                  target="_blank"
                  rel="noreferrer"
                  className="border border-ink/20 px-6 py-3 text-sm font-semibold text-ink transition hover:border-ink/50"
                >
                  Репозиторий
                </a>
              </div>
            </div>

            <div className="animate-rise-late min-h-[420px] overflow-hidden rounded-[28px] shadow-soft lg:min-h-[560px]">
              <ProductStage />
            </div>
          </div>
        </section>

        <div className="section-rule" />

        <section id="how" className="mx-auto max-w-6xl px-6 py-20 sm:py-24">
          <p className="text-xs uppercase tracking-[0.22em] text-sea">Один сценарий</p>
          <h2 className="mt-3 max-w-2xl font-display text-3xl text-ink sm:text-4xl">
            Вопрос врача → поиск по базе → ответ с источником
          </h2>
          <p className="mt-4 max-w-2xl text-ink/65">
            Система поднимает релевантные фрагменты клинических документов, ранжирует их по
            источнику, свежести и evidence level, затем формирует ответ через GigaChat.
          </p>

          <ol className="mt-12 grid gap-8 sm:grid-cols-3">
            {[
              {
                n: "01",
                t: "Запрос",
                d: "Врач пишет вопрос в API или Telegram.",
              },
              {
                n: "02",
                t: "Retrieval",
                d: "ChromaDB + multilingual-e5 находят релевантные чанки.",
              },
              {
                n: "03",
                t: "Ответ",
                d: "GigaChat отвечает только по найденному контексту.",
              },
            ].map((item) => (
              <li key={item.n} className="border-t border-ink/10 pt-5">
                <p className="font-display text-2xl text-sea">{item.n}</p>
                <h3 className="mt-3 text-lg font-semibold">{item.t}</h3>
                <p className="mt-2 text-sm leading-relaxed text-ink/65">{item.d}</p>
              </li>
            ))}
          </ol>
        </section>

        <div className="section-rule" />

        <section id="stack" className="mx-auto max-w-6xl px-6 py-20 sm:py-24">
          <p className="text-xs uppercase tracking-[0.22em] text-sea">Стек</p>
          <h2 className="mt-3 font-display text-3xl text-ink sm:text-4xl">
            Что уже работает в проекте
          </h2>
          <div className="mt-10 grid gap-x-10 gap-y-6 text-sm text-ink/75 sm:grid-cols-2">
            <p>
              <span className="font-semibold text-ink">Backend:</span> FastAPI, RAG Engine,
              ChromaDB, sentence-transformers, GigaChat
            </p>
            <p>
              <span className="font-semibold text-ink">Интерфейсы:</span> OpenAPI docs, Telegram-бот,
              этот лендинг
            </p>
            <p>
              <span className="font-semibold text-ink">Знания:</span> тестовые клинические документы
              + Obsidian vault
            </p>
            <p>
              <span className="font-semibold text-ink">Репозиторий:</span>{" "}
              <a className="underline decoration-sea/40 underline-offset-4" href={GITHUB_URL}>
                github.com/dimitry8st-prog/MedBot-AI
              </a>
            </p>
          </div>
        </section>
      </main>

      <footer className="border-t border-ink/10 bg-mist">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-10 text-sm text-ink/60 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="font-display text-lg text-ink">MedBot AI</p>
            <p className="mt-2 max-w-xl">
              Справочный характер. Не заменяет консультацию врача и клиническое решение
              специалиста.
            </p>
          </div>
          <p>© {new Date().getFullYear()}</p>
        </div>
      </footer>
    </div>
  );
}
