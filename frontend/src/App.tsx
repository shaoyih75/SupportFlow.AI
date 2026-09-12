import { useMemo, useState } from 'react'
import './App.css'

type Document = { id: string; title: string; icon: string; type: string; updated: string; content: string; accent: string }

const documents: Document[] = [
  { id: 'welcome', title: 'Welcome to Northstar', icon: '✦', type: 'Getting started', updated: 'Just now', accent: 'violet', content: 'A calm, shared home for the way your team thinks.' },
  { id: 'handbook', title: 'Team handbook', icon: '▤', type: 'Company', updated: '2 hours ago', accent: 'blue', content: 'How we work together, make decisions, and keep momentum.' },
  { id: 'roadmap', title: 'Product roadmap', icon: '◈', type: 'Product', updated: 'Yesterday', accent: 'coral', content: 'A living view of what we are building next.' },
  { id: 'research', title: 'Customer research', icon: '⌁', type: 'Research', updated: 'Sep 08', accent: 'yellow', content: 'Patterns, questions, and decisions from our conversations.' },
]

const outlines = ['A shared home', 'What is Northstar?', 'The workspace rhythm', 'Start with one page']

function App() {
  const [activeId, setActiveId] = useState('welcome')
  const [query, setQuery] = useState('')
  const [isStarred, setIsStarred] = useState(true)
  const [draft, setDraft] = useState('')
  const active = documents.find((document) => document.id === activeId) ?? documents[0]
  const filteredDocuments = useMemo(() => documents.filter((document) => document.title.toLowerCase().includes(query.toLowerCase())), [query])

  return <div className="document-app">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">N</span><span>northstar</span><span className="brand-dot">.</span></div>
      <button className="workspace-select"><span className="workspace-icon">N</span><span><b>Northstar Inc.</b><small>Personal workspace</small></span><span className="chevron">⌄</span></button>
      <div className="side-actions"><label className="search-input"><span>⌕</span><input aria-label="Search pages" placeholder="Search pages..." value={query} onChange={(event) => setQuery(event.target.value)} /><kbd>⌘ K</kbd></label><button><span>＋</span> New page</button></div>
      <nav className="document-nav" aria-label="Workspace navigation"><p className="side-label">Workspace</p><button className="nav-link active"><span>▦</span> All pages <b>24</b></button><button className="nav-link"><span>☆</span> Favorites</button><button className="nav-link"><span>♧</span> Shared with me</button><p className="side-label pages-label">Your pages</p>{filteredDocuments.map((document) => <button key={document.id} className={`page-link ${activeId === document.id ? 'selected' : ''}`} onClick={() => setActiveId(document.id)}><span className={`page-icon ${document.accent}`}>{document.icon}</span>{document.title}<i>•••</i></button>)}</nav>
      <div className="sidebar-footer"><button className="nav-link"><span>♧</span> Templates</button><button className="nav-link"><span>⚙</span> Settings</button><div className="profile"><span className="avatar">JW</span><span><b>Jamie Wilson</b><small>Admin</small></span><span className="more">•••</span></div></div>
    </aside>
    <main className="main-area">
      <header className="topbar"><div className="breadcrumbs"><span>Workspace</span><b>/</b><strong>{active.title}</strong></div><div className="top-actions"><span className="saved"><i /> Saved</span><button className="icon-button" aria-label="Share document">♧</button><button className="icon-button" aria-label="More options">•••</button><button className="publish-button">Share <span>↗</span></button></div></header>
      <div className="editor-layout">
        <article className="editor"><div className="editor-meta"><span className="doc-type">{active.type}</span><button className={`star-button ${isStarred ? 'starred' : ''}`} onClick={() => setIsStarred(!isStarred)} aria-label="Toggle favorite">★</button></div><h1>{active.title}</h1><p className="lead">{active.content}</p><div className="author-row"><span className="avatar">JW</span><span>Jamie Wilson <small>· edited just now</small></span><span className="read-time">4 min read</span></div><div className="rule" /><section className="document-copy"><h2>A shared home for clear thinking</h2><p>Northstar brings your team's knowledge, plans, and decisions into one quiet place. Every page is easy to find, simple to update, and connected to the work around it.</p><blockquote>“The best workspace is the one that makes the next right thing obvious.”</blockquote><h2>What is Northstar?</h2><p>Think of a workspace as a living library. Start with a page, invite the people who need it, and let the structure emerge as your team learns. There is no perfect system to design before the first idea lands.</p><div className="callout"><span>✦</span><div><strong>Small start</strong><p>Create one useful page today. A handbook, a plan, or a decision log is enough.</p></div></div><h2>The workspace rhythm</h2><p>Pages stay useful when they have an owner, a clear title, and a little room to change. Keep the context close to the decision and the decision close to the people doing the work.</p></section><div className="comment-box"><span className="comment-icon">＋</span><input placeholder="Add a comment..." value={draft} onChange={(event) => setDraft(event.target.value)} /><button disabled={!draft.trim()}>Comment</button></div></article>
        <aside className="right-rail"><div className="rail-block"><p className="rail-label">On this page</p>{outlines.map((item, index) => <button key={item} className={index === 0 ? 'outline-active' : ''}>{item}</button>)}</div><div className="rail-block activity"><p className="rail-label">Recent activity</p><div><span className="activity-dot violet-dot" /><p><b>Jamie</b> created this page<small>Just now</small></p></div><div><span className="activity-dot blue-dot" /><p><b>Alex</b> viewed the page<small>12 min ago</small></p></div><div><span className="activity-dot coral-dot" /><p><b>Jamie</b> updated the title<small>Yesterday</small></p></div></div><div className="rail-tip"><span>✦</span><strong>Make it yours</strong><p>Invite teammates and turn this page into a shared point of view.</p><button>Invite people ↗</button></div></aside>
      </div>
    </main>
  </div>
}
export default App
