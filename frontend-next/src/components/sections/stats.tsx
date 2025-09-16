'use client'

const stats = [
  { id: 1, name: 'Active Internships', value: '2,500+' },
  { id: 2, name: 'Partner Companies', value: '450+' },
  { id: 3, name: 'Students Placed', value: '1,200+' },
  { id: 4, name: 'Success Rate', value: '89%' },
]

export function Stats() {
  return (
    <section className="bg-white py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl lg:max-w-none">
          <div className="text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Trusted by students across Canada
            </h2>
            <p className="mt-4 text-lg leading-8 text-gray-600">
              Join thousands of students who have found their perfect internship through our platform
            </p>
          </div>
          <dl className="mt-16 grid grid-cols-1 gap-0.5 overflow-hidden rounded-2xl text-center sm:grid-cols-2 lg:grid-cols-4">
            {stats.map((stat) => (
              <div key={stat.id} className="flex flex-col bg-gray-400/5 p-8">
                <dt className="text-sm font-semibold leading-6 text-gray-600">{stat.name}</dt>
                <dd className="order-first text-3xl font-bold tracking-tight text-gray-900">
                  {stat.value}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </section>
  )
}
