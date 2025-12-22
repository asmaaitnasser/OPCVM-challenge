const types = [
  {
    title: "OPCVM Actions",
    desc: "Investissement majoritaire en actions cotées en bourse.",
  },
  {
    title: "OPCVM Obligations",
    desc: "Focus sur les titres de créance et obligations.",
  },
  {
    title: "OPCVM Monétaires",
    desc: "Placement à court terme dans des instruments monétaires.",
  },
];

export default function OpcvmTypes() {
  return (
    <section className="py-24 bg-gray-50">
      <div className="max-w-6xl mx-auto px-6">

        <h2 className="text-3xl font-bold mb-12">
          Types d’OPCVM au Maroc
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {types.map((t, i) => (
            <div
              key={i}
              className="bg-white rounded-xl border border-gray-100 shadow-sm p-8"
            >
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
