export default function Mission() {
  return (
    <section className="py-24 bg-gray-50">
      <div className="max-w-6xl mx-auto px-6">

        <div className="bg-white rounded-2xl p-12 shadow-sm border border-gray-100">
          <div className="flex items-start gap-6">

            {/* Icône */}
            <div className="w-12 h-12 flex items-center justify-center rounded-lg bg-red-100 text-red-600 text-xl font-bold">
              ◎
            </div>

            {/* Contenu */}
            <div>
              <h2 className="text-2xl font-bold mb-4">
                Notre Mission
              </h2>
              <p className="text-gray-600 leading-relaxed max-w-3xl">
                FundWatch AI transforme les données brutes de performance OPCVM
                en insights actionnables grâce au Machine Learning.
                <br /><br />
                Nous aidons les gestionnaires de fonds, risk managers et comités
                d’investissement à anticiper les risques et à prendre des décisions
                éclairées en temps réel.
              </p>
            </div>

          </div>
        </div>

      </div>
    </section>
  );
}
