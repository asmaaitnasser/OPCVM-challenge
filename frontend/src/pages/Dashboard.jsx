import { Routes, Route, Link, Navigate } from "react-router-dom";

// Composants pour chaque section
function Overview() {
  return <div className="p-6"><h2>Overview</h2></div>;
}

function AnomalyDaily() {
  return <div className="p-6"><h2>Anomaly Daily</h2></div>;
}

function AnomalyWeekly() {
  return <div className="p-6"><h2>Anomaly Weekly</h2></div>;
}

function Projection1Jour() {
  return <div className="p-6"><h2>Projection 1 jour</h2></div>;
}

function Projection30Jours() {
  return <div className="p-6"><h2>Projection 30 jours</h2></div>;
}

function Recommendations() {
  return <div className="p-6"><h2>Recommendations</h2></div>;
}

function WafaVsMarket() {
  return <div className="p-6"><h2>Wafa vs Market</h2></div>;
}

export default function Dashboard() {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r">
        <div className="p-4">
          <h1 className="text-xl font-bold mb-6">Dashboard</h1>
          <nav className="space-y-1">
            <Link 
              to="/dashboard/overview" 
              className="block px-4 py-2 bg-red-600 text-white rounded"
            >
              Overview
            </Link>
            <Link 
              to="/dashboard/anomaly-daily" 
              className="block px-4 py-2 hover:bg-gray-100 rounded"
            >
              Anomaly Daily
            </Link>
            <Link 
              to="/dashboard/anomaly-weekly" 
              className="block px-4 py-2 hover:bg-gray-100 rounded"
            >
              Anomaly Weekly
            </Link>
            <div className="pl-4 pt-2">
              <p className="text-sm text-gray-500 mb-2">Prediction Risque</p>
              <Link 
                to="/dashboard/projection-1-jour" 
                className="block px-4 py-2 hover:bg-gray-100 rounded text-sm"
              >
                Projection 1 jour
              </Link>
              <Link 
                to="/dashboard/projection-30-jours" 
                className="block px-4 py-2 hover:bg-gray-100 rounded text-sm"
              >
                Projection 30 jours
              </Link>
            </div>
            <Link 
              to="/dashboard/recommendations" 
              className="block px-4 py-2 hover:bg-gray-100 rounded"
            >
              Recommendations
            </Link>
            <Link 
              to="/dashboard/wafa-vs-market" 
              className="block px-4 py-2 hover:bg-gray-100 rounded"
            >
              Wafa vs Market
            </Link>
          </nav>
        </div>
      </aside>

      {/* Contenu principal */}
      <main className="flex-1 bg-gray-50">
        <Routes>
          {/* Redirection par défaut vers overview */}
          <Route path="/" element={<Navigate to="/dashboard/overview" replace />} />
          <Route path="/overview" element={<Overview />} />
          <Route path="/anomaly-daily" element={<AnomalyDaily />} />
          <Route path="/anomaly-weekly" element={<AnomalyWeekly />} />
          <Route path="/projection-1-jour" element={<Projection1Jour />} />
          <Route path="/projection-30-jours" element={<Projection30Jours />} />
          <Route path="/recommendations" element={<Recommendations />} />
          <Route path="/wafa-vs-market" element={<WafaVsMarket />} />
        </Routes>
      </main>
    </div>
  );
}