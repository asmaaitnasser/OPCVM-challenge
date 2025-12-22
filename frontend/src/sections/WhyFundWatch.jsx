const items = [
  {
    title: "Gain de temps considérable",
    desc: "Automatisation complète de la collecte et de l’analyse des données.",
  },
  {
    title: "Anticipation du risque",
    desc: "Projection à 30 jours pour une gestion proactive.",
  },
  {
    title: "Décisions data-driven",
    desc: "Analyses quantitatives basées sur des modèles ML.",
  },
  {
    title: "Interfaces adaptées par rôle",
    desc: "Vues dédiées aux gestionnaires, risk managers et comités.",
  },
];

export default function WhyFundWatch() {
  return (
    <section className="py-24 bg-gray-50">
      <div className="max-w-6xl mx-auto px-6">

        <h2 className="text-4xl font-bold text-center mb-4">
          Pourquoi FundWatch AI ?
        </h2>
        <p className="text-center text-gray-600 mb-16">
          Les avantages concrets pour votre gestion de portefeuille
        </p>

        {/* 👇 LA vraie différence est ici */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {items.map((item, i) => (
            <div
              key={i}
              className="
                bg-white
                rounded-xl
                shadow-md
                p-8
                border border-gray-100
              "
            >
              <h3 className="text-lg font-semibold mb-3">
                {item.title}
              </h3>
              <p className="text-gray-600 leading-relaxed">
                {item.desc}
              </p>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
