/**
 * PageWrapper.jsx — consistent page padding and title.
 */
export default function PageWrapper({ title, children }) {
  return (
    <main className="flex-1 overflow-y-auto">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
        {title && <h2 className="mb-5 text-gray-800">{title}</h2>}
        {children}
      </div>
    </main>
  )
}
