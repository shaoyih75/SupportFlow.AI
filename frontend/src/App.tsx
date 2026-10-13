import { useMemo, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import './App.css'

type Status = 'Ready' | 'Processing' | 'Needs attention'
type View = 'overview' | 'documents' | 'activity'
type IconName = 'grid' | 'file' | 'clock' | 'search' | 'plus' | 'upload' | 'sparkle' | 'more' | 'arrow' | 'chevron' | 'bell' | 'check' | 'warning' | 'members' | 'settings' | 'logout' | 'folder' | 'link' | 'close'
type Doc = { id: number; title: string; type: 'PDF' | 'DOCX' | 'URL'; size: string; updated: string; status: Status; color: string; owner: string }

const initialDocuments: Doc[] = [
  { id: 1, title: 'Employee Handbook', type: 'PDF', size: '2.4 MB', updated: '12 min ago', status: 'Ready', color: 'coral', owner: 'You' },
  { id: 2, title: 'Product Strategy 2026', type: 'DOCX', size: '840 KB', updated: 'Yesterday', status: 'Ready', color: 'blue', owner: 'Maya Chen' },
  { id: 3, title: 'Customer Research Notes', type: 'PDF', size: '5.1 MB', updated: '2 days ago', status: 'Processing', color: 'violet', owner: 'Noah Williams' },
  { id: 4, title: 'Engineering Runbook', type: 'URL', size: '12 pages', updated: 'Sep 8', status: 'Ready', color: 'green', owner: 'You' },
  { id: 5, title: 'Security Guidelines', type: 'PDF', size: '1.2 MB', updated: 'Sep 4', status: 'Needs attention', color: 'amber', owner: 'Ari Patel' },
]

const activities = [
  { name: 'Maya Chen', action: 'uploaded Product Strategy 2026', time: 'Yesterday', initials: 'MC', tone: 'pink' },
  { name: 'SupportFlow AI', action: 'finished processing Employee Handbook', time: '12 min ago', initials: 'AI', tone: 'purple' },
  { name: 'Noah Williams', action: 'started processing Customer Research Notes', time: '2 days ago', initials: 'NW', tone: 'blue' },
]

function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  const paths: Record<IconName, ReactNode> = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/></>,
    file: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h6"/></>,
    clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>, search: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
    plus: <path d="M12 5v14M5 12h14"/>, upload: <><path d="M12 16V4M7 9l5-5 5 5"/><path d="M5 20h14"/></>,
    sparkle: <><path d="m12 3 1.2 4.1L17 9l-3.8 1.9L12 15l-1.2-4.1L7 9l3.8-1.9z"/><path d="m5 15 .7 2.3L8 18.5l-2.3 1.2L5 22l-.7-2.3L2 18.5l2.3-1.2z"/></>,
    more: <><circle cx="5" cy="12" r="1" fill="currentColor"/><circle cx="12" cy="12" r="1" fill="currentColor"/><circle cx="19" cy="12" r="1" fill="currentColor"/></>, arrow: <><path d="M5 12h14M14 7l5 5-5 5"/></>, chevron: <path d="m9 18 6-6-6-6"/>,
    bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/></>, check: <path d="m5 12 4 4L19 6"/>, warning: <><path d="M12 4 3 20h18L12 4z"/><path d="M12 9v4M12 17h.01"/></>,
    members: <><circle cx="9" cy="8" r="3"/><path d="M3 20c0-4 2-6 6-6s6 2 6 6"/><path d="M16 5a3 3 0 0 1 0 6M17 14c3 .4 4 2.4 4 6"/></>,
    settings: <><circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 0 0-.1-1l2-1.6-2-3.4-2.5 1a8 8 0 0 0-1.7-1L14.4 3h-4.8L9.2 6a8 8 0 0 0-1.7 1L5 6 3 9.4 5.1 11a7 7 0 0 0 0 2L3 14.6 5 18l2.5-1a8 8 0 0 0 1.7 1l.4 3h4.8l.4-3a8 8 0 0 0 1.7-1l2.5 1 2-3.4-2.1-1.6a7 7 0 0 0 .1-1z"/></>,
    logout: <><path d="M10 17l5-5-5-5M15 12H3"/><path d="M13 4h6a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-6"/></>, folder: <path d="M3 6h7l2 2h9v11H3z"/>,
    link: <><path d="M10 13a5 5 0 0 0 7.5.5l2-2a5 5 0 0 0-7-7l-1.2 1.2"/><path d="M14 11a5 5 0 0 0-7.5-.5l-2 2a5 5 0 0 0 7 7l1.2-1.2"/></>, close: <path d="m6 6 12 12M18 6 6 18"/>,
  }
  return <svg className="icon" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>
}

function App() {
  const [view, setView] = useState<View>('overview')
  const [query, setQuery] = useState('')
  const [documents, setDocuments] = useState(initialDocuments)
  const [showUpload, setShowUpload] = useState(false)
  const [showAsk, setShowAsk] = useState(false)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [dragging, setDragging] = useState(false)
  const visibleDocuments = useMemo(() => documents.filter((doc) => doc.title.toLowerCase().includes(query.toLowerCase())), [documents, query])
  const readyCount = documents.filter((doc) => doc.status === 'Ready').length

  function addDocument(title = 'Quarterly Planning Notes.pdf') {
    const cleanTitle = title.replace(/\.[^.]+$/, '')
    setDocuments((items) => [{ id: Date.now(), title: cleanTitle, type: 'PDF', size: '1.8 MB', updated: 'Just now', status: 'Processing', color: 'violet', owner: 'You' }, ...items])
    setShowUpload(false)
  }
  function ask(event: FormEvent) {
    event.preventDefault()
    if (question.trim()) setAnswer('Employees receive 20 days of paid time off each year. Unused time can roll over up to 5 days, subject to manager approval.')
  }

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-logo"><Icon name="sparkle" size={16}/></span><span>SupportFlow</span><b>AI</b></div>
      <button className="workspace-switcher"><span className="workspace-avatar">A</span><span><strong>Acme Inc.</strong><small>Team workspace</small></span><Icon name="chevron" size={14}/></button>
      <nav aria-label="Primary navigation">
        <p className="nav-label">Workspace</p>
        <button className={view === 'overview' ? 'active' : ''} onClick={() => setView('overview')}><Icon name="grid"/>Overview</button>
        <button className={view === 'documents' ? 'active' : ''} onClick={() => setView('documents')}><Icon name="file"/>Documents<span className="count">{documents.length}</span></button>
        <button className={view === 'activity' ? 'active' : ''} onClick={() => setView('activity')}><Icon name="clock"/>Activity</button>
        <p className="nav-label manage">Manage</p><button><Icon name="members"/>Members</button><button><Icon name="settings"/>Settings</button>
      </nav>
      <div className="sidebar-foot">
        <div className="plan-card"><span><Icon name="sparkle" size={14}/></span><strong>Free plan</strong><p>{documents.length} of 25 documents used</p><div><i style={{ width: `${Math.min(documents.length / 25 * 100, 100)}%` }}/></div><button>View plans <Icon name="arrow" size={13}/></button></div>
        <div className="profile"><span>HT</span><div><strong>Haoxuan Tong</strong><small>haoxuan@acme.co</small></div><button aria-label="Sign out"><Icon name="logout" size={16}/></button></div>
      </div>
    </aside>

    <main>
      <header className="topbar"><label className="global-search"><Icon name="search" size={17}/><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search your workspace..."/><kbd>⌘ K</kbd></label><div className="top-actions"><button className="notification" aria-label="Notifications"><Icon name="bell"/><i/></button><span className="divider"/><button className="top-avatar">HT</button></div></header>
      <div className="content">
        <section className="welcome-row"><div><p className="eyebrow">Sunday, October 11</p><h1>{view === 'documents' ? 'Documents' : view === 'activity' ? 'Workspace activity' : 'Good morning, Haoxuan'}<span>.</span></h1><p>{view === 'documents' ? 'Your team’s source of truth, all in one place.' : view === 'activity' ? 'See what has changed across your workspace.' : 'Here’s what’s happening in your workspace today.'}</p></div><button className="primary" onClick={() => setShowUpload(true)}><Icon name="plus" size={17}/>Add document</button></section>

        {view === 'overview' && <><section className="stat-grid">
          <div className="stat-card"><span className="stat-icon lilac"><Icon name="file"/></span><p>Total documents</p><strong>{documents.length}</strong><small><b>+2</b> this week</small></div>
          <div className="stat-card"><span className="stat-icon mint"><Icon name="check"/></span><p>Ready to search</p><strong>{readyCount}</strong><small>{Math.round(readyCount / documents.length * 100)}% of documents</small></div>
          <div className="stat-card"><span className="stat-icon peach"><Icon name="clock"/></span><p>Processing</p><strong>{documents.filter((d) => d.status === 'Processing').length}</strong><small>Usually takes 2–5 min</small></div>
          <div className="stat-card"><span className="stat-icon sky"><Icon name="sparkle"/></span><p>Questions asked</p><strong>38</strong><small><b>+12</b> this week</small></div>
        </section><section className="ask-banner"><div className="ask-art"><span/><i/><b><Icon name="sparkle" size={26}/></b></div><div><span className="new-pill">AI SEARCH</span><h2>Ask your workspace anything.</h2><p>Get clear answers grounded in your team’s documents, with sources you can trust.</p><button onClick={() => setShowAsk(true)}>Ask a question <Icon name="arrow" size={15}/></button></div><div className="question-preview"><span><Icon name="sparkle" size={15}/></span><div><small>TRY ASKING</small><p>“What is our parental leave policy?”</p></div></div></section></>}

        {view !== 'activity' && <section className={`documents-panel ${view === 'documents' ? 'full' : ''}`}><div className="section-head"><div><h2>{view === 'documents' ? 'All documents' : 'Recent documents'}</h2><p>{view === 'documents' ? `${visibleDocuments.length} documents in this workspace` : 'Your latest uploaded and updated files'}</p></div>{view === 'overview' && <button onClick={() => setView('documents')}>View all <Icon name="arrow" size={14}/></button>}</div><div className="table-wrap"><table><thead><tr><th>Document</th><th>Status</th><th>Owner</th><th>Last updated</th><th/></tr></thead><tbody>{visibleDocuments.slice(0, view === 'overview' ? 4 : undefined).map((doc) => <tr key={doc.id}><td><span className={`file-icon ${doc.color}`}>{doc.type === 'URL' ? <Icon name="link" size={18}/> : <Icon name="file" size={18}/>}</span><div><strong>{doc.title}</strong><small>{doc.type} · {doc.size}</small></div></td><td><span className={`status ${doc.status.toLowerCase().replace(' ', '-')}`}><i/>{doc.status}</span></td><td><span className="owner-dot">{doc.owner === 'You' ? 'HT' : doc.owner.split(' ').map((x) => x[0]).join('')}</span>{doc.owner}</td><td>{doc.updated}</td><td><button className="more" aria-label={`Options for ${doc.title}`}><Icon name="more"/></button></td></tr>)}</tbody></table>{visibleDocuments.length === 0 && <div className="empty"><Icon name="search" size={28}/><strong>No documents found</strong><p>Try a different search term.</p></div>}</div></section>}

        {view === 'overview' && <section className="lower-grid"><div className="activity-card"><div className="section-head"><div><h2>Recent activity</h2><p>Updates from your team</p></div><button onClick={() => setView('activity')}>View all</button></div>{activities.map((item) => <ActivityItem key={item.action} item={item}/>)}</div><div className="quick-card"><div className="section-head"><div><h2>Quick actions</h2><p>Get things moving</p></div></div><button onClick={() => setShowUpload(true)}><span className="lilac"><Icon name="upload"/></span><div><strong>Upload a document</strong><small>PDF, DOCX, TXT, or a web link</small></div><Icon name="chevron" size={16}/></button><button onClick={() => setShowAsk(true)}><span className="sky"><Icon name="sparkle"/></span><div><strong>Ask a question</strong><small>Search across ready documents</small></div><Icon name="chevron" size={16}/></button></div></section>}
        {view === 'activity' && <section className="activity-page">{activities.concat([{ name: 'You', action: 'created the Acme Inc. workspace', time: 'Sep 1', initials: 'HT', tone: 'green' }]).map((item) => <ActivityItem key={item.action} item={item}/>)}</section>}
      </div>
    </main>

    {showUpload && <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && setShowUpload(false)}><section className="modal"><button className="modal-close" onClick={() => setShowUpload(false)}><Icon name="close"/></button><span className="modal-icon"><Icon name="upload"/></span><h2>Add a document</h2><p>Upload a file and SupportFlow AI will make it searchable.</p><div className={`drop-zone ${dragging ? 'dragging' : ''}`} onDragOver={(e) => {e.preventDefault(); setDragging(true)}} onDragLeave={() => setDragging(false)} onDrop={(e) => {e.preventDefault(); setDragging(false); addDocument(e.dataTransfer.files[0]?.name)}}><Icon name="folder" size={28}/><strong>Drop your file here</strong><span>or click to browse · PDF, DOCX, TXT up to 25 MB</span><input type="file" aria-label="Choose a file" onChange={(e) => addDocument(e.target.files?.[0]?.name)}/></div><div className="modal-or"><span/>or add a web link<span/></div><form onSubmit={(e) => {e.preventDefault(); addDocument('Imported web page')}}><label>Web address</label><div className="url-row"><input type="url" placeholder="https://example.com/article"/><button>Add link</button></div></form></section></div>}
    {showAsk && <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && setShowAsk(false)}><section className="modal ask-modal"><button className="modal-close" onClick={() => setShowAsk(false)}><Icon name="close"/></button><span className="modal-icon ai"><Icon name="sparkle"/></span><h2>Ask your workspace</h2><p>Answers are generated only from ready documents.</p><form onSubmit={ask}><textarea autoFocus value={question} onChange={(e) => {setQuestion(e.target.value); setAnswer('')}} placeholder="What would you like to know?"/><button className="ask-submit" disabled={!question.trim()}>Ask SupportFlow <Icon name="arrow" size={15}/></button></form>{answer && <div className="answer"><small>ANSWER</small><p>{answer}</p><button><Icon name="file" size={14}/> Employee Handbook · p. 18</button></div>}</section></div>}
  </div>
}

function ActivityItem({ item }: { item: { name: string; action: string; time: string; initials: string; tone: string } }) {
  return <div className="activity-item"><span className={`person ${item.tone}`}>{item.initials}</span><p><strong>{item.name}</strong> {item.action}<small>{item.time}</small></p></div>
}

export default App
