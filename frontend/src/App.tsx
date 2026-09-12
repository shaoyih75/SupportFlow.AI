import { useMemo, useState } from 'react'
import './App.css'

type Status = 'open' | 'pending' | 'resolved'
type Ticket = { id: string; customer: string; initials: string; subject: string; preview: string; status: Status; priority: 'high' | 'normal'; channel: 'Email' | 'Chat'; time: string; tag: string }

const tickets: Ticket[] = [
  { id: 'SF-1048', customer: 'Ava Thompson', initials: 'AT', subject: 'Unable to sync my workspace', preview: 'The sync has been running for more than 20 minutes...', status: 'open', priority: 'high', channel: 'Email', time: '8 min ago', tag: 'Integrations' },
  { id: 'SF-1047', customer: 'Marcus Chen', initials: 'MC', subject: 'Invoice shows the wrong plan', preview: 'I upgraded last week but this month still shows...', status: 'pending', priority: 'normal', channel: 'Chat', time: '24 min ago', tag: 'Billing' },
  { id: 'SF-1046', customer: 'Sofia Ramirez', initials: 'SR', subject: 'How do I add a teammate?', preview: 'Looking for the right permissions to invite our...', status: 'open', priority: 'normal', channel: 'Email', time: '42 min ago', tag: 'Account' },
  { id: 'SF-1045', customer: 'Noah Williams', initials: 'NW', subject: 'Export completed successfully', preview: 'Thanks for the quick help. Everything is working...', status: 'resolved', priority: 'normal', channel: 'Chat', time: '1 hr ago', tag: 'Exports' },
  { id: 'SF-1044', customer: 'Lina Patel', initials: 'LP', subject: 'API rate limit question', preview: 'Could you clarify how the burst limit is calculated?', status: 'resolved', priority: 'normal', channel: 'Email', time: '2 hrs ago', tag: 'API' },
]
const statusLabels: Record<Status, string> = { open: 'Open', pending: 'Pending', resolved: 'Resolved' }

function App() {
  const [selectedId, setSelectedId] = useState('SF-1048')
  const [filter, setFilter] = useState<'all' | Status>('all')
  const [search, setSearch] = useState('')
  const [draft, setDraft] = useState('')
  const visibleTickets = useMemo(() => tickets.filter((ticket) => {
    const matchesFilter = filter === 'all' || ticket.status === filter
    return matchesFilter && `${ticket.subject} ${ticket.customer} ${ticket.id}`.toLowerCase().includes(search.toLowerCase())
  }), [filter, search])
  const selectedTicket = tickets.find((ticket) => ticket.id === selectedId) ?? tickets[0]

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">S</span><span>supportflow</span><span className="brand-dot">.</span></div>
      <div className="workspace-switcher"><span className="workspace-icon">N</span><span><strong>Northstar Inc.</strong><small>Support workspace</small></span><span className="chevron">⌄</span></div>
      <nav className="primary-nav" aria-label="Main navigation"><p className="nav-label">Workspace</p><button className="nav-item active"><span>▦</span> Inbox <b>12</b></button><button className="nav-item"><span>◷</span> All tickets</button><button className="nav-item"><span>☆</span> Reports</button><p className="nav-label">Manage</p><button className="nav-item"><span>♙</span> Customers</button><button className="nav-item"><span>⚙</span> Settings</button></nav>
      <div className="sidebar-bottom"><div className="plan-card"><span className="spark">✦</span><strong>Pro plan</strong><span>72% used</span><div className="progress"><i /></div></div><div className="profile"><span className="avatar me">JW</span><span><strong>Jamie Wilson</strong><small>Admin</small></span><span className="more">•••</span></div></div>
    </aside>
    <main className="main-content">
      <header className="topbar"><div><p className="eyebrow">Tuesday, September 10, 2024</p><h1>Good morning, Jamie <span>✦</span></h1></div><div className="top-actions"><button className="icon-button" aria-label="Notifications">♧<i /></button><button className="help-button">?</button><button className="new-ticket">＋ New ticket</button></div></header>
      <section className="metrics" aria-label="Support metrics"><div className="metric-card"><span className="metric-icon coral">◒</span><div><small>Open tickets</small><strong>12</strong><em className="up">↑ 8.2%</em></div><span className="sparkline coral-line">╱╲╱╲╱╲╱</span></div><div className="metric-card"><span className="metric-icon blue">◷</span><div><small>Avg. first response</small><strong>18m</strong><em className="down">↓ 12.4%</em></div><span className="sparkline blue-line">╲╱╲╱╲╱╲</span></div><div className="metric-card"><span className="metric-icon yellow">◉</span><div><small>Resolution rate</small><strong>94.6%</strong><em className="up">↑ 3.1%</em></div><span className="sparkline yellow-line">╱╱╲╱╲╱</span></div></section>
      <section className="inbox-layout">
        <div className="ticket-panel"><div className="panel-heading"><div><h2>Inbox</h2><span>{visibleTickets.length} tickets need your attention</span></div><button className="filter-button">Filter <span>⌄</span></button></div><div className="ticket-toolbar"><div className="search-box"><span>⌕</span><input aria-label="Search tickets" placeholder="Search tickets..." value={search} onChange={(event) => setSearch(event.target.value)} /></div><div className="filter-tabs">{(['all', 'open', 'pending', 'resolved'] as const).map((value) => <button key={value} className={filter === value ? 'selected' : ''} onClick={() => setFilter(value)}>{value === 'all' ? 'All' : statusLabels[value]}</button>)}</div></div><div className="ticket-list">{visibleTickets.map((ticket) => <button key={ticket.id} className={`ticket-row ${selectedId === ticket.id ? 'selected' : ''}`} onClick={() => setSelectedId(ticket.id)}><span className="avatar">{ticket.initials}</span><span className="ticket-copy"><strong>{ticket.customer}</strong><span>{ticket.subject}</span><small>{ticket.preview}</small></span><span className="ticket-meta"><time>{ticket.time}</time><span className={`status ${ticket.status}`}>{ticket.status === 'open' && <i />}{statusLabels[ticket.status]}</span></span></button>)}</div><button className="load-more">Load more tickets <span>↓</span></button></div>
        <div className="detail-panel"><div className="detail-header"><div><span className="ticket-id">{selectedTicket.id} · {selectedTicket.channel}</span><h2>{selectedTicket.subject}</h2></div><button className="more-button">•••</button></div><div className="detail-tags"><span className={`status ${selectedTicket.status}`}><i /> {statusLabels[selectedTicket.status]}</span><span className="tag">{selectedTicket.tag}</span><span className="priority">{selectedTicket.priority === 'high' ? 'High priority' : 'Normal priority'}</span></div><div className="conversation"><div className="message customer-message"><span className="avatar coral-avatar">{selectedTicket.initials}</span><div><div className="message-meta"><strong>{selectedTicket.customer}</strong><time>8 min ago</time></div><p>Hi team, I have been trying to sync my workspace for the past 20 minutes, but it still appears to be processing. Is there something I should check on my end?</p></div></div><div className="message agent-message"><span className="avatar me">JW</span><div><div className="message-meta"><strong>You</strong><time>just now</time></div><p>Hi Ava, thanks for flagging this. I’m checking the sync status now and will get you an update shortly.</p></div></div></div><div className="reply-box"><textarea placeholder="Write a reply..." value={draft} onChange={(event) => setDraft(event.target.value)} /><div className="reply-actions"><span><button aria-label="Add attachment">⌕</button><button aria-label="Add emoji">☺</button></span><button className="send-button" disabled={!draft.trim()}>Send reply <span>↗</span></button></div></div></div>
      </section>
    </main>
  </div>
}
export default App
