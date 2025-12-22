const steps = [
  {
    step: "Étape 1",
    title: "Collecte des données",
    desc: "Scraping quotidien et hebdomadaire des performances ASFIM.",
  },
  {
    step: "Étape 2",
    title: "Prétraitement",
    desc: "Nettoyage, normalisation et formatage des données brutes.",
  },
  {
    step: "Étape 3",
    title: "Feature Engineering",
    desc: "Calcul des indicateurs : volatilité, drawdown, momentum.",
  },
  {
    step: "Étape 4",
    title: "Détection anomalies",
    desc: "Isolation Forest et règles métier sur données daily et weekly.",
  },
  {
    step: "Étape 5",
    title: "Scoring de risque",
    desc: "Classification NORMAL / LOW / MEDIUM / HIGH par fonds.",
  },
  {
    step: "Étape 6",
    title: "Projection ML",
    desc: "Random Forest pour prédire le risque à 30 jours.",
  },
  {
    step: "Étape 7",
    title: "Comparaison marché",
    desc: "Benchmark Wafa Gestion vs marché global.",
  },
  {
    step: "Étape 8",
    title: "Recommandations",
    desc: "Actions : REDUCE / MONITOR / STABLE.",
  },
];

export default function Pipeline() {
  return (
    <section className="py-24 bg-white">
      <div className="max-w-6xl mx-auto px-6">

        <h2 className="text-4xl font-bold text-center mb-4">
          Notre Pipeline d’Analyse
        </h2>
        <p className="text-center text-gray-600 mb-16">
          Un processus automatisé en 8 étapes pour transformer les données en décisions
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {steps.map((s, i) => (
            <div
              key={i}
              className="bg-gray-50 rounded-xl p-8 shadow-sm border border-gray-100"
            >
              <span className="text-sm text-red-600 font-medium">
                {s.step}
              </span>
              <h3 className="text-lg font-semibold mt-2 mb-2">
                {s.title}
              </h3>
              <p className="text-gray-600">
                {s.desc}
              </p>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
