import { Link } from "react-router-dom";
export default function Navbar() {
  return (
    <nav className="fixed top-0 w-full z-50 bg-white border-b">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-red-600 rounded-md text-white flex items-center justify-center font-bold">
            F
          </div>
          <span className="font-semibold text-lg">FundWatch AI</span>
        </div>

        <div className="hidden md:flex gap-8 text-sm text-gray-600">
          <a href="#opcvm" className="hover:text-black">Qu'est-ce qu’un OPCVM ?</a>
          <a href="#platform" className="hover:text-black">La Plateforme</a>
          <a href="#pipeline" className="hover:text-black">Notre Pipeline</a>
        </div>

        <Link
  to="/dashboard"
  className="bg-black text-white px-4 py-2 rounded-lg"
>
  Accéder au Dashboard
</Link>
      </div>
    </nav>
  );
}
