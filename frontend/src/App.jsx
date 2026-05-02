import { useState, useEffect } from 'react'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://alfaleus-project.onrender.com/api/v1'
const API_KEY = import.meta.env.VITE_API_KEY || 'supersecretapikey'

function App() {
  const [clusters, setClusters] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(0)
  const [totalClusters, setTotalClusters] = useState(0)
  const [categories, setCategories] = useState([])
  const [subscriptions, setSubscriptions] = useState([])
  const [savedArticles, setSavedArticles] = useState([])
  const [savedArticleIds, setSavedArticleIds] = useState([])
  const [stats, setStats] = useState({ last_updated: null, sources: 0 })
  const [selectedCategory, setSelectedCategory] = useState('All')
  const LIMIT = 8

  useEffect(() => {
    const fetchDigest = async () => {
      try {
        setLoading(true)
        
        // Fetch categories
        const catRes = await axios.get(`${API_BASE_URL}/categories`, {
          headers: { 'X-API-KEY': API_KEY }
        })
        setCategories(['All', ...catRes.data])

        // Fetch subscriptions
        const subRes = await axios.get(`${API_BASE_URL}/subscriptions`, {
          headers: { 'X-API-KEY': API_KEY }
        })
        setSubscriptions(subRes.data)

        // Fetch saved articles
        const savedRes = await axios.get(`${API_BASE_URL}/articles/saved`, {
          headers: { 'X-API-KEY': API_KEY }
        })
        setSavedArticles(savedRes.data)
        setSavedArticleIds(savedRes.data.map(a => a.id))

        // Fetch stats
        const statsRes = await axios.get(`${API_BASE_URL}/stats`, {
          headers: { 'X-API-KEY': API_KEY }
        })
        setStats(statsRes.data)

        if (selectedCategory === 'Saved') {
          setClusters([])
          setTotalClusters(savedRes.data.length)
        } else {
          // Fetch count for selected category
          const countRes = await axios.get(`${API_BASE_URL}/digest/count?category=${selectedCategory}`, {
            headers: { 'X-API-KEY': API_KEY }
          })
          setTotalClusters(countRes.data.total)

          const response = await axios.get(`${API_BASE_URL}/digest?skip=${page * LIMIT}&limit=${LIMIT}&category=${selectedCategory}`, {
            headers: {
              'X-API-KEY': API_KEY
            }
          })
          setClusters(response.data)
        }
        setError(null)
      } catch (err) {
        console.error('API Error:', err)
        setError(
          err.response?.data?.detail || 
          err.message || 
          'Failed to connect to the news server'
        )
      } finally {
        setLoading(false)
      }
    }

    fetchDigest()
  }, [page, selectedCategory])

  const getPageNumbers = () => {
    const totalPages = Math.ceil(totalClusters / LIMIT)
    const pages = []
    
    if (totalPages <= 7) {
      for (let i = 0; i < totalPages; i++) pages.push(i)
    } else {
      pages.push(0)
      
      if (page > 3) pages.push('...')
      
      const start = Math.max(1, page - 1)
      const end = Math.min(totalPages - 2, page + 1)
      
      for (let i = start; i <= end; i++) {
        if (!pages.includes(i)) pages.push(i)
      }
      
      if (page < totalPages - 4) pages.push('...')
      
      if (!pages.includes(totalPages - 1)) pages.push(totalPages - 1)
    }
    return pages
  }

  const formatLastUpdated = (dateStr) => {
    if (!dateStr) return 'Just now'
    const lastRun = new Date(dateStr)
    const now = new Date()
    const diffMins = Math.floor((now - lastRun) / 60000)
    if (diffMins < 1) return 'Just now'
    if (diffMins === 1) return '1 min ago'
    return `${diffMins} mins ago`
  }

  const toggleSaveArticle = async (e, articleId) => {
    e.stopPropagation()
    try {
      if (savedArticleIds.includes(articleId)) {
        await axios.delete(`${API_BASE_URL}/articles/${articleId}/save`, {
          headers: { 'X-API-KEY': API_KEY }
        })
        setSavedArticleIds(prev => prev.filter(id => id !== articleId))
        setSavedArticles(prev => prev.filter(a => a.id !== articleId))
      } else {
        const saveRes = await axios.post(`${API_BASE_URL}/articles/${articleId}/save`, {}, {
          headers: { 'X-API-KEY': API_KEY }
        })
        setSavedArticleIds(prev => [...prev, articleId])
        // Optionally refetch or find in clusters to add to savedArticles
        if (selectedCategory === 'Saved') fetchDigest()
      }
    } catch (err) {
      console.error("Save failed", err)
    }
  }

  const toggleSubscription = async (e, cat) => {
    e.stopPropagation()
    if (cat === 'All') return
    
    try {
      if (subscriptions.includes(cat)) {
        await axios.delete(`${API_BASE_URL}/subscriptions/${cat}`, {
          headers: { 'X-API-KEY': API_KEY }
        })
        setSubscriptions(prev => prev.filter(s => s !== cat))
      } else {
        await axios.post(`${API_BASE_URL}/subscriptions/${cat}`, {}, {
          headers: { 'X-API-KEY': API_KEY }
        })
        setSubscriptions(prev => [...prev, cat])
      }
    } catch (err) {
      console.error("Subscription failed", err)
    }
  }

  if (loading) return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-50 text-slate-800">
      <div className="relative">
        <div className="absolute inset-0 rounded-full blur-xl bg-emerald-400/20 animate-pulse"></div>
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-emerald-500 relative z-10"></div>
      </div>
      <p className="mt-6 text-emerald-600 font-medium animate-pulse font-outfit tracking-wide">Synthesizing your daily digest...</p>
    </div>
  )

  if (error) return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-50 p-4 relative overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-rose-500/10 rounded-full blur-3xl"></div>
      <div className="bg-white/80 backdrop-blur-xl p-10 rounded-3xl shadow-xl max-w-md w-full text-center border border-rose-200 relative z-10">
        <div className="text-rose-500 text-6xl mb-6">⚠️</div>
        <h2 className="text-3xl font-black text-slate-900 mb-3 font-outfit">Connection Error</h2>
        <p className="text-slate-600 mb-8">{error}</p>
        <button 
          onClick={() => window.location.reload()}
          className="w-full bg-gradient-to-r from-rose-500 to-pink-500 hover:from-rose-600 hover:to-pink-600 text-white font-bold py-4 px-6 rounded-xl transition-all duration-300 shadow-md shadow-rose-500/20 hover:shadow-rose-500/30 hover:-translate-y-1"
        >
          Try Again
        </button>
        <p className="mt-6 text-xs text-slate-400 font-mono">Ensure backend is running at {API_BASE_URL}</p>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-slate-50 pb-24 selection:bg-emerald-500/20 relative">
      {/* Dynamic Background Effects */}
      <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-1/2 h-1/2 bg-emerald-400/10 blur-[120px] rounded-full mix-blend-multiply"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-1/2 h-1/2 bg-cyan-400/10 blur-[120px] rounded-full mix-blend-multiply"></div>
      </div>

      <div className="relative z-10">
        {/* Hero Section */}
        <div className="border-b border-slate-200/60 py-16 mb-12 bg-white/40 backdrop-blur-3xl shadow-sm">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex flex-col md:flex-row justify-between items-center gap-8">
              <div className="text-center md:text-left">
                <h1 className="text-6xl md:text-7xl font-black tracking-tight mb-4 font-outfit">
                  <span className="text-slate-900">Insight</span>
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-500 to-cyan-500 drop-shadow-sm">Matrix</span>
                </h1>
                <p className="text-slate-500 text-xl max-w-xl font-light leading-relaxed">
                  High-signal news, clustered by AI and synthesized for clarity.
                </p>
                <div className="flex items-center gap-6 mt-6">
                  <div className="flex items-center gap-2 text-sm font-medium text-slate-400">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    Last updated: {formatLastUpdated(stats.last_updated)}
                  </div>
                  <div className="flex items-center gap-2 text-sm font-medium text-slate-400">
                    <span className="w-2 h-2 rounded-full bg-cyan-500"></span>
                    Fetched from {stats.sources} sources
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-5 bg-white/80 backdrop-blur-md px-6 py-4 rounded-2xl border border-slate-200 shadow-md">
                <div className="text-transparent bg-clip-text bg-gradient-to-br from-emerald-500 to-cyan-500 font-black text-5xl font-outfit">{clusters.length}</div>
                <div className="text-slate-500 text-sm font-medium tracking-wider uppercase leading-snug">Trending<br/>Topics</div>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-6">
          <div 
            className="flex overflow-x-auto pb-6 mb-8 gap-3 snap-x" 
            style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
          >
            {/* Special "Saved" Category */}
            <button
              onClick={() => {
                setSelectedCategory('Saved');
                setPage(0);
              }}
              className={`snap-start whitespace-nowrap px-8 py-3.5 rounded-full font-bold text-sm transition-all shadow-sm border flex items-center gap-3 ${
                selectedCategory === 'Saved'
                  ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white border-transparent scale-105 shadow-amber-200'
                  : 'bg-white/70 backdrop-blur-xl border-slate-200/80 text-slate-600 hover:bg-white hover:text-amber-600'
              }`}
            >
              🔖 Saved
            </button>

            {categories.map((cat) => (
                <div key={`cat-wrapper-${cat}`} className="relative group/nav shrink-0">
                  <button
                    onClick={() => {
                      setSelectedCategory(cat);
                      setPage(0);
                    }}
                    className={`snap-start whitespace-nowrap px-8 py-3.5 rounded-full font-bold text-sm transition-all shadow-sm border flex items-center gap-3 ${
                      selectedCategory === cat
                        ? 'bg-gradient-to-r from-emerald-500 to-cyan-500 text-white border-transparent scale-105 shadow-emerald-200'
                        : 'bg-white/70 backdrop-blur-xl border-slate-200/80 text-slate-600 hover:bg-white hover:text-emerald-600'
                    }`}
                  >
                    {cat}
                    {cat !== 'All' && (
                      <span 
                        onClick={(e) => toggleSubscription(e, cat)}
                        className={`text-lg transition-transform hover:scale-125 ${
                          subscriptions.includes(cat) ? 'text-yellow-400 fill-yellow-400' : 'text-slate-300 opacity-0 group-hover/nav:opacity-100'
                        }`}
                      >
                        {subscriptions.includes(cat) ? '★' : '☆'}
                      </span>
                    )}
                  </button>
                </div>
              ))}
            </div>

          {selectedCategory === 'Saved' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {savedArticles.map(article => (
                /* Reusing article card layout */
                <div 
                  key={`saved-${article.id}`} 
                  className="group flex flex-col bg-white/70 backdrop-blur-xl rounded-3xl border border-slate-200/80 overflow-hidden hover:bg-white transition-all duration-500 shadow-sm hover:shadow-[0_20px_40px_-15px_rgba(0,0,0,0.1)] hover:-translate-y-2"
                >
                    <div className="p-8 flex flex-col h-full">
                      <div className="flex justify-between items-center mb-6">
                        <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-widest bg-emerald-50 border border-emerald-100 px-3 py-1.5 rounded-full">
                          {article.source}
                        </span>
                        <button 
                          onClick={(e) => toggleSaveArticle(e, article.id)}
                          className="p-2 rounded-xl text-amber-500 bg-amber-50 border border-amber-200 hover:scale-110 transition-all shadow-sm"
                        >
                          <svg viewBox="0 0 24 24" className="w-5 h-5 fill-current" stroke="currentColor" strokeWidth="2">
                            <path d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                            <path d="M8 7h3" strokeLinecap="round" />
                          </svg>
                        </button>
                      </div>
                      <h3 className="text-2xl font-bold text-slate-900 mb-5 line-clamp-3 group-hover:text-emerald-600 transition-colors duration-300 leading-snug font-outfit">
                        <a href={article.url} target="_blank" rel="noopener noreferrer">
                          {article.title}
                        </a>
                      </h3>
                      <div className="bg-slate-100/50 p-5 rounded-2xl mb-8 border-l-4 border-emerald-500/30 group-hover:bg-slate-100 transition-colors">
                        <p className="text-slate-800 text-[15px] leading-relaxed line-clamp-4 group-hover:line-clamp-none font-medium transition-all duration-300">
                          {article.summary}
                        </p>
                      </div>
                      <div className="flex justify-between items-center mt-auto pt-4 border-t border-slate-100">
                        <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wide">
                          {new Date(article.published_at).toLocaleDateString()}
                        </div>
                        <a href={article.url} target="_blank" className="text-cyan-600 text-xs font-bold">Read Article →</a>
                      </div>
                    </div>
                  </div>
                ))}
              {savedArticleIds.length === 0 && (
                <div className="col-span-full py-24 text-center">
                  <p className="text-slate-400 font-medium">No saved articles yet. Bookmark some stories to see them here!</p>
                </div>
              )}
            </div>
          ) : clusters.length > 0 ? (
            <div className="space-y-20">
              {clusters.map((cluster) => (
                <section key={cluster.id} id={`topic-${cluster.id}`} className="relative scroll-mt-24">
                  <div className="flex items-center mb-10 group">
                    <div className="h-12 w-2 bg-gradient-to-b from-emerald-500 to-cyan-500 rounded-full mr-5 shadow-sm"></div>
                    <h2 className="text-4xl font-extrabold text-slate-900 tracking-tight font-outfit transition-colors group-hover:text-emerald-700 break-words">
                      {cluster.topic_name}
                    </h2>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {cluster.articles.map((article) => (
                      <div 
                        key={article.id} 
                        className="group flex flex-col bg-white/70 backdrop-blur-xl rounded-3xl border border-slate-200/80 overflow-hidden hover:bg-white transition-all duration-500 shadow-sm hover:shadow-[0_20px_40px_-15px_rgba(0,0,0,0.1)] hover:-translate-y-2"
                      >
                        <div className="p-8 flex flex-col h-full">
                          <div className="flex justify-between items-center mb-6">
                            <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-widest bg-emerald-50 border border-emerald-100 px-3 py-1.5 rounded-full">
                              {article.source}
                            </span>
                            {article.sentiment && (
                              <div className="flex items-center gap-3">
                                <div className="flex items-center bg-slate-50 px-3 py-1.5 rounded-full border border-slate-100">
                                  <span className={`w-2 h-2 rounded-full mr-2 ${
                                    article.sentiment === 'positive' ? 'bg-emerald-500' :
                                    article.sentiment === 'negative' ? 'bg-rose-500' :
                                    'bg-amber-500'
                                  }`}></span>
                                  <span className="text-[10px] font-bold text-slate-600 uppercase tracking-widest">
                                    {article.sentiment}
                                  </span>
                                </div>
                                <button 
                                  onClick={(e) => toggleSaveArticle(e, article.id)}
                                  className={`p-2 rounded-xl transition-all hover:scale-110 ${
                                    savedArticleIds.includes(article.id)
                                      ? 'text-amber-500 bg-amber-50 border border-amber-200'
                                      : 'text-slate-300 hover:text-slate-400 bg-slate-50 border border-slate-100'
                                  }`}
                                >
                                  <svg viewBox="0 0 24 24" className="w-5 h-5 fill-current" stroke="currentColor" strokeWidth="2">
                                    <path d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                                    <path d="M8 7h3" strokeLinecap="round" />
                                  </svg>
                                </button>
                              </div>
                            )}
                          </div>
                          
                          <h3 className="text-2xl font-bold text-slate-900 mb-5 line-clamp-3 group-hover:text-emerald-600 transition-colors duration-300 leading-snug font-outfit">
                            <a href={article.url} target="_blank" rel="noopener noreferrer">
                              {article.title}
                            </a>
                          </h3>
                          
                          <div className="bg-slate-100/50 p-5 rounded-2xl mb-8 border-l-4 border-emerald-500/30 group-hover:bg-slate-100 transition-colors">
                            <p className="text-slate-800 text-[15px] leading-relaxed line-clamp-4 group-hover:line-clamp-none font-medium transition-all duration-300">
                              {article.summary || "Summary pending analysis..."}
                            </p>
                          </div>
                          
                          <div className="flex justify-between items-center mt-auto pt-4 border-t border-slate-100">
                            <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wide">
                              {new Date(article.published_at).toLocaleDateString('en-US', {
                                month: 'short',
                                day: 'numeric',
                                year: 'numeric'
                              })}
                            </div>
                            <a 
                              href={article.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-cyan-600 text-xs font-bold hover:text-cyan-700 transition-all inline-flex items-center group/btn"
                            >
                              <span className="relative">
                                Read Article
                                <span className="absolute bottom-0 left-0 w-0 h-[1px] bg-cyan-600 group-hover/btn:w-full transition-all duration-300"></span>
                              </span>
                              <svg className="w-4 h-4 ml-1 transform group-hover/btn:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                              </svg>
                            </a>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              ))}
              
              {/* Pagination Controls */}
              <div className="flex justify-between items-center mt-16 pt-8 border-t border-slate-200/60 pb-12">
                <button
                  onClick={() => setPage(p => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="px-6 py-3 rounded-xl bg-white border border-slate-200 text-slate-700 font-medium hover:bg-slate-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm flex items-center gap-2"
                >
                  &larr; Prev
                </button>
                
                <div className="flex gap-2 items-center">
                  {getPageNumbers().map((p, idx) => (
                    p === '...' ? (
                      <span key={`dots-${idx}`} className="px-2 text-slate-400 font-bold">...</span>
                    ) : (
                      <button
                        key={`page-${p}`}
                        onClick={() => setPage(p)}
                        className={`w-10 h-10 rounded-xl font-bold transition-all shadow-sm ${
                          page === p 
                            ? 'bg-emerald-500 text-white scale-110 shadow-emerald-200' 
                            : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        {p + 1}
                      </button>
                    )
                  ))}
                </div>

                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={page >= Math.ceil(totalClusters / LIMIT) - 1}
                  className="px-6 py-3 rounded-xl bg-white border border-slate-200 text-slate-700 font-medium hover:bg-slate-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm flex items-center gap-2"
                >
                  Next &rarr;
                </button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-32 bg-white/70 backdrop-blur-xl rounded-3xl border border-slate-200 text-center shadow-lg relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-50 to-transparent"></div>
              <div className="text-7xl mb-6 relative z-10 drop-shadow-sm">📰</div>
              <h3 className="text-3xl font-bold text-slate-900 mb-3 font-outfit relative z-10">No signals detected</h3>
              <p className="text-slate-500 max-w-sm relative z-10">Your personalized news matrix is awaiting its first data stream. Please trigger the collector.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
