import React, { useState, useEffect } from 'react'

const NewsCard = ({ article }) => (
  <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
    <div className="flex justify-between items-start mb-4">
      <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded">
        {article.source}
      </span>
      <div className={`w-2 h-2 rounded-full ${article.sentiment === 'positive' ? 'bg-green-500' : 'bg-yellow-500'}`} />
    </div>
    <h3 className="text-xl font-bold mb-2">{article.title}</h3>
    <p className="text-slate-600 text-sm">{article.summary}</p>
  </div>
)

function App() {
  return (
    <div className="min-h-screen">
      <header className="p-6"><h1>InsightMatrix</h1></header>
      <main className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
        <NewsCard article={{title: "Sample News", source: "Reuters", summary: "Brief summary..."}} />
      </main>
    </div>
  )
}
export default App
