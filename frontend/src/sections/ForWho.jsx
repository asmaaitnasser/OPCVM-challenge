const targets = [
  {
    id: "1",
    title: "Gestionnaires de fonds",
    desc: "Surveillez vos portefeuilles et ajustez vos allocations en fonction du risque.",
  },
  {
    id: "2",
    title: "Risk Managers",
    desc: "Identifiez les risques émergents avant qu’ils ne se matérialisent.",
  },
  {
    id: "3",
    title: "Comités d’investissement",
    desc: "Prenez des décisions stratégiques basées sur des données objectives.",
  },
];

export default function ForWho() {
  return (
    <section className="py-24 bg-white">
      <div className="max-w-6xl mx-auto px-6">

        <h2 className="text-3xl font-bold mb-4">
          Pour qui ?
        </h2>
        <p className="text-gray-600 mb-16">
          Des interfaces et analyses adaptées à chaque profil
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {targets.map((t) => (
            <div
              key={t.id}
              className="bg-gray-50 rounded-xl p-8 border border-gray-100 shadow-sm"
            >
              <div className="w-8 h-8 flex items-center justify-center rounded-full bg-red-100 text-red-600 font-semibold mb-4">
                {t.id}
              </div>
              <h3 className="text-lg font-semibold mb-2">
                {t.title}
              </h3>
              <p className="text-gray-600">
                {t.desc}
              </p>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
