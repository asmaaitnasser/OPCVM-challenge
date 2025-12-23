export default function Mission() {
  const featuresTop = [
    {
      icon: "!",
      iconBg: "bg-red-50",
      iconText: "text-red-600",
      title: "Détection d'anomalies",
      desc:
        "Identification automatique des comportements anormaux sur les données quotidiennes et hebdomadaires grâce à l'Isolation Forest et aux z-scores.",
      border: "border-red-200",
    },
    {
      icon: "▥",
      iconBg: "bg-green-50",
      iconText: "text-green-600",
      title: "Scoring de risque",
      desc:
        "Attribution d'un score de risque (NORMAL, LOW, MEDIUM, HIGH) basé sur l'agrégation des anomalies et indicateurs clés de performance.",
      border: "border-green-200",
    },
    {
      icon: "↗",
      iconBg: "bg-amber-50",
      iconText: "text-amber-600",
      title: "Projection 30 jours",
      desc:
        "Prédiction du niveau de risque futur à horizon 1 mois avec probabilités associées, alimentée par des modèles Random Forest.",
      border: "border-amber-200",
    },
  ];

  const featuresBottom = [
    {
      icon: "▦",
      iconBg: "bg-red-50",
      iconText: "text-red-600",
      title: "Analyse comparative",
      desc:
        "Benchmarking automatique : comparez les performances et le risque de Wafa Gestion par rapport au marché global.",
      border: "border-red-200",
    },
    {
      icon: "!",
      iconBg: "bg-red-50",
      iconText: "text-red-600",
      title: "Alertes en temps réel",
      desc:
        "Notifications instantanées sur les fonds présentant des anomalies critiques ou une dégradation du score de risque.",
      border: "border-red-200",
    },
    {
      icon: "?",
      iconBg: "bg-green-50",
      iconText: "text-green-600",
      title: "Recommandations",
      desc:
        "Suggestions actionnables : REDUCE (réduire l'exposition), MONITOR (surveiller de près), STABLE (situation normale).",
      border: "border-green-200",
    },
  ];

  return (
    <section className="py-24 bg-gray-50">
      <div className="max-w-6xl mx-auto px-6">
        {/* Mission */}
        <div className="bg-white rounded-2xl p-12 shadow-sm border border-gray-100">
          <div className="flex items-start gap-6">
            <div className="w-12 h-12 flex items-center justify-center rounded-lg bg-red-100 text-red-600 text-xl font-bold">
              ◎
            </div>

            <div>
              <h2 className="text-2xl font-bold mb-4">Notre Mission</h2>
              <p className="text-gray-600 leading-relaxed max-w-3xl">
                FundWatch AI transforme les données brutes de performance OPCVM
                en insights actionnables grâce au Machine Learning.
                <br />
                <br />
                Nous aidons les gestionnaires de fonds, risk managers et comités
                d’investissement à anticiper les risques et à prendre des décisions
                éclairées en temps réel.
              </p>
            </div>
          </div>
        </div>

        {/* Cards row 1 */}
        <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-6">
          {featuresTop.map((f) => (
            <div
              key={f.title}
              className={`bg-white rounded-2xl p-6 shadow-sm border ${f.border}`}
            >
              <div
                className={`w-11 h-11 rounded-xl ${f.iconBg} ${f.iconText} flex items-center justify-center font-bold`}
              >
                {f.icon}
              </div>
              <h3 className="mt-4 font-semibold text-lg">{f.title}</h3>
              <p className="mt-2 text-gray-600 leading-relaxed text-sm">
                {f.desc}
              </p>
            </div>
          ))}
        </div>

        {/* Cards row 2 */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
          {featuresBottom.map((f) => (
            <div
              key={f.title}
              className={`bg-white rounded-2xl p-6 shadow-sm border ${f.border}`}
            >
              <div
                className={`w-11 h-11 rounded-xl ${f.iconBg} ${f.iconText} flex items-center justify-center font-bold`}
              >
                {f.icon}
              </div>
              <h3 className="mt-4 font-semibold text-lg">{f.title}</h3>
              <p className="mt-2 text-gray-600 leading-relaxed text-sm">
                {f.desc}
              </p>
            </div>
          ))}
        </div>

        {/* ❌ PAS DE "POUR QUI" */}
      </div>
    </section>
  );
}
