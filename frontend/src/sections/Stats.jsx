export default function Stats() {
  return (
    <section className="py-20 bg-white">
      <div className="max-w-6xl mx-auto px-6 grid grid-cols-1 md:grid-cols-3 gap-12 text-center">

        <div className="bg-gray-50 p-8 rounded-xl shadow">
          <div className="text-4xl font-bold">300+</div>
          <p className="text-gray-500 mt-2">Fonds analysés</p>
        </div>

        <div className="bg-gray-50 p-8 rounded-xl shadow">
          <div className="text-4xl font-bold">98%</div>
          <p className="text-gray-500 mt-2">Précision ML</p>
        </div>

        <div className="bg-gray-50 p-8 rounded-xl shadow">
          <div className="text-4xl font-bold">30j</div>
          <p className="text-gray-500 mt-2">Projection risque</p>
        </div>

      </div>
    </section>
  );
}
