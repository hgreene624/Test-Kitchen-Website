import Link from 'next/link'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm lg:flex">
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-8">
            Chef Candidate Evaluation Platform
          </h1>
          <p className="text-xl mb-12">
            Welcome to the chef candidate evaluation system
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/candidate/signup"
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Candidate Sign Up
            </Link>
            <Link
              href="/candidate/login"
              className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition"
            >
              Candidate Login
            </Link>
            <Link
              href="/admin/login"
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
            >
              Admin Login
            </Link>
          </div>
        </div>
      </div>
    </main>
  )
}
