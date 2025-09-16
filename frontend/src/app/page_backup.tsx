"use client";

import { useState, useEffect } from "react";
import { Search, MapPin, Filter, Briefcase, Clock, DollarSign, Mail, ExternalLink, X, ChevronDown } from "lucide-react";

interface ContactEmail {
  id: number;
  email: string;
  confidence_score: number;
  confidence_level: string;
  email_type: string;
  name?: string;
  title?: string;
  mx_verified: boolean;
}

interface Internship {
  id: number;
  title: string;
  company: {
    id: number;
    name: string;
    domain: string;
    logo_url: string;
    description: string;
    headquarters_city: string;
    headquarters_region: string;
    headquarters_country: string;
    size_category: string;
    industry: string;
  };
  description: string;
  field_tag: string;
  city: string;
  region: string;
  country: string;
  modality: string;
  salary_min: number;
  salary_max: number;
  salary_currency: string;
  duration_months: number;
  apply_url: string;
  posted_at: string;
  expires_at: string;
  skills_required: string[];
  education_level: string;
  experience_level: string;
  government_program: boolean;
  relevance_score: number;
  created_at: string;
  source: {
    id: number;
    name: string;
    display_name: string;
    source_type: string;
  };
}

interface InternshipDetail extends Internship {
  contact_emails: ContactEmail[];
  is_bookmarked: boolean;
}

export default function Home() {
  const [internships, setInternships] = useState<Internship[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedField, setSelectedField] = useState("");
  const [selectedLocation, setSelectedLocation] = useState("");
  const [selectedModality, setSelectedModality] = useState("");
  const [minSalary, setMinSalary] = useState("");
  const [selectedInternship, setSelectedInternship] = useState<InternshipDetail | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const searchInternships = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('q', searchQuery);
      if (selectedField) params.append('field', selectedField);
      if (selectedLocation) params.append('city', selectedLocation);
      if (selectedModality) params.append('modality', selectedModality);
      if (minSalary) params.append('salary_min', minSalary);

      const response = await fetch(`http://localhost:8000/api/internships?${params}`);
      const data = await response.json();
      setInternships(data.items || []);
    } catch (error) {
      console.error('Error fetching internships:', error);
      setInternships([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    searchInternships();
  }, []);

  const handleInternshipClick = async (internshipId: number) => {
    try {
      const response = await fetch(`http://localhost:8000/api/internships/${internshipId}`);
      const data = await response.json();
      setSelectedInternship(data);
    } catch (error) {
      console.error('Error fetching internship details:', error);
    }
  };

  const formatSalary = (min: number, max: number, currency: string) => {
    return `$${min.toLocaleString()} - $${max.toLocaleString()} ${currency}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-CA', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getModalityColor = (modality: string) => {
    switch (modality) {
      case 'remote': return 'bg-[#50FA7B] text-[#282A36]';
      case 'hybrid': return 'bg-[#FFB86C] text-[#282A36]';
      case 'on_site': return 'bg-[#FF79C6] text-[#282A36]';
      default: return 'bg-[#6272A4] text-[#F8F8F2]';
    }
  };

  const getFieldColor = (field: string) => {
    const colors = {
      'software_engineering': 'bg-[#8BE9FD] text-[#282A36]',
      'data_science': 'bg-[#BD93F9] text-[#282A36]',
      'product_management': 'bg-[#FFB86C] text-[#282A36]',
      'design_ux_ui': 'bg-[#FF79C6] text-[#282A36]',
      'marketing': 'bg-[#50FA7B] text-[#282A36]',
    };
    return colors[field as keyof typeof colors] || 'bg-[#6272A4] text-[#F8F8F2]';
  };

  return (
    <div className="min-h-screen bg-[#282A36] text-[#F8F8F2]">
      {/* Header */}
      <div className="bg-[#44475A] border-b border-[#6272A4]">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-[#50FA7B]">EasyInterns</h1>
              <p className="text-[#6272A4] mt-1">Find your perfect Canadian internship</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-sm text-[#6272A4]">Total Opportunities</div>
                <div className="text-2xl font-bold text-[#8BE9FD]">{internships.length}</div>
              </div>
            </div>
          </div>

          {/* Search Bar */}
          <div className="relative mb-4">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-[#6272A4] h-5 w-5" />
            <input
              type="text"
              placeholder="Search internships, companies, or skills..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && searchInternships()}
              className="w-full pl-12 pr-4 py-4 bg-[#282A36] border border-[#6272A4] rounded-xl text-[#F8F8F2] placeholder-[#6272A4] focus:border-[#8BE9FD] focus:outline-none transition-colors"
            />
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 px-4 py-2 bg-[#6272A4] text-[#F8F8F2] rounded-lg hover:bg-[#7A8BB8] transition-colors"
          >
            <Filter className="h-4 w-4" />
            Filters
            <ChevronDown className={`h-4 w-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </button>

          {/* Filters */}
          {showFilters && (
            <div className="mt-4 p-4 bg-[#282A36] rounded-xl border border-[#6272A4]">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-[#F8F8F2] mb-2">Field</label>
                  <select
                    value={selectedField}
                    onChange={(e) => setSelectedField(e.target.value)}
                    className="w-full px-3 py-2 bg-[#44475A] border border-[#6272A4] rounded-lg text-[#F8F8F2] focus:border-[#8BE9FD] focus:outline-none"
                  >
                    <option value="">All Fields</option>
                    <option value="software_engineering">Software Engineering</option>
                    <option value="data_science">Data Science</option>
                    <option value="product_management">Product Management</option>
                    <option value="design_ux_ui">UX/UI Design</option>
                    <option value="marketing">Marketing</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#F8F8F2] mb-2">Location</label>
                  <select
                    value={selectedLocation}
                    onChange={(e) => setSelectedLocation(e.target.value)}
                    className="w-full px-3 py-2 bg-[#44475A] border border-[#6272A4] rounded-lg text-[#F8F8F2] focus:border-[#8BE9FD] focus:outline-none"
                  >
                    <option value="">All Locations</option>
                    <option value="Toronto">Toronto</option>
                    <option value="Vancouver">Vancouver</option>
                    <option value="Montreal">Montreal</option>
                    <option value="Calgary">Calgary</option>
                    <option value="Ottawa">Ottawa</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#F8F8F2] mb-2">Work Style</label>
                  <select
                    value={selectedModality}
                    onChange={(e) => setSelectedModality(e.target.value)}
                    className="w-full px-3 py-2 bg-[#44475A] border border-[#6272A4] rounded-lg text-[#F8F8F2] focus:border-[#8BE9FD] focus:outline-none"
                  >
                    <option value="">All Types</option>
                    <option value="remote">Remote</option>
                    <option value="hybrid">Hybrid</option>
                    <option value="on_site">On-site</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#F8F8F2] mb-2">Min Salary</label>
                  <input
                    type="number"
                    placeholder="e.g. 20000"
                    value={minSalary}
                    onChange={(e) => setMinSalary(e.target.value)}
                    className="w-full px-3 py-2 bg-[#44475A] border border-[#6272A4] rounded-lg text-[#F8F8F2] placeholder-[#6272A4] focus:border-[#8BE9FD] focus:outline-none"
                  />
                </div>
              </div>
              <div className="mt-4 flex gap-3">
                <button
                  onClick={searchInternships}
                  className="px-6 py-2 bg-[#50FA7B] text-[#282A36] rounded-lg hover:bg-[#5FFF8A] font-semibold transition-colors"
                >
                  Apply Filters
                </button>
                <button
                  onClick={() => {
                    setSelectedField("");
                    setSelectedLocation("");
                    setSelectedModality("");
                    setMinSalary("");
                    setSearchQuery("");
                    searchInternships();
                  }}
                  className="px-6 py-2 bg-[#6272A4] text-[#F8F8F2] rounded-lg hover:bg-[#7A8BB8] transition-colors"
                >
                  Clear All
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#8BE9FD]"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {internships.map((internship) => (
              <div
                key={internship.id}
                onClick={() => handleInternshipClick(internship.id)}
                className="bg-[#44475A] rounded-xl p-6 border border-[#6272A4] hover:border-[#8BE9FD] transition-all cursor-pointer hover:shadow-lg hover:shadow-[#8BE9FD]/10"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <img
                      src={internship.company.logo_url}
                      alt={internship.company.name}
                      className="w-12 h-12 rounded-lg object-cover bg-[#282A36]"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(internship.company.name)}&background=6272A4&color=F8F8F2&size=48`;
                      }}
                    />
                    <div>
                      <h3 className="font-semibold text-[#F8F8F2] text-lg">{internship.title}</h3>
                      <p className="text-[#8BE9FD] font-medium">{internship.company.name}</p>
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getFieldColor(internship.field_tag)}`}>
                    {internship.field_tag.replace('_', ' ').toUpperCase()}
                  </span>
                </div>

                <p className="text-[#6272A4] text-sm mb-4 line-clamp-2">
                  {internship.description}
                </p>

                <div className="space-y-2 mb-4">
                  <div className="flex items-center gap-2 text-sm">
                    <MapPin className="h-4 w-4 text-[#FF79C6]" />
                    <span className="text-[#F8F8F2]">{internship.city}, {internship.region}</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getModalityColor(internship.modality)}`}>
                      {internship.modality.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <DollarSign className="h-4 w-4 text-[#50FA7B]" />
                    <span className="text-[#F8F8F2]">{formatSalary(internship.salary_min, internship.salary_max, internship.salary_currency)}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <Clock className="h-4 w-4 text-[#FFB86C]" />
                    <span className="text-[#F8F8F2]">{internship.duration_months} months</span>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 mb-4">
                  {internship.skills_required.slice(0, 3).map((skill, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-[#282A36] text-[#8BE9FD] rounded-md text-xs border border-[#6272A4]"
                    >
                      {skill}
                    </span>
                  ))}
                  {internship.skills_required.length > 3 && (
                    <span className="px-2 py-1 bg-[#282A36] text-[#6272A4] rounded-md text-xs border border-[#6272A4]">
                      +{internship.skills_required.length - 3} more
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-between text-xs text-[#6272A4]">
                  <span>Posted {formatDate(internship.posted_at)}</span>
                  <span className="flex items-center gap-1">
                    <Briefcase className="h-3 w-3" />
                    {internship.source.display_name}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && internships.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-xl font-semibold text-[#F8F8F2] mb-2">No internships found</h3>
            <p className="text-[#6272A4]">Try adjusting your search criteria or filters</p>
          </div>
        )}
      </div>

      {/* Modal */}
      {selectedInternship && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-[#44475A] rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-4">
                  <img
                    src={selectedInternship.company.logo_url}
                    alt={selectedInternship.company.name}
                    className="w-16 h-16 rounded-xl object-cover bg-[#282A36]"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(selectedInternship.company.name)}&background=6272A4&color=F8F8F2&size=64`;
                    }}
                  />
                  <div>
                    <h2 className="text-2xl font-bold text-[#F8F8F2] mb-1">{selectedInternship.title}</h2>
                    <p className="text-[#8BE9FD] text-lg font-semibold">{selectedInternship.company.name}</p>
                    <p className="text-[#6272A4] text-sm">{selectedInternship.company.industry} • {selectedInternship.company.size_category}</p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedInternship(null)}
                  className="text-[#6272A4] hover:text-[#F8F8F2] transition-colors"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-[#F8F8F2] mb-3">Job Description</h3>
                    <p className="text-[#F8F8F2] leading-relaxed">{selectedInternship.description}</p>
                  </div>

                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-[#F8F8F2] mb-3">Required Skills</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedInternship.skills_required.map((skill, index) => (
                        <span
                          key={index}
                          className="px-3 py-1 bg-[#282A36] text-[#8BE9FD] rounded-lg text-sm border border-[#6272A4]"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>

                  {selectedInternship.contact_emails.length > 0 && (
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold text-[#F8F8F2] mb-3">Contact Information</h3>
                      <div className="space-y-3">
                        {selectedInternship.contact_emails.map((contact) => (
                          <div key={contact.id} className="bg-[#282A36] p-4 rounded-lg border border-[#6272A4]">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <Mail className="h-4 w-4 text-[#8BE9FD]" />
                                <span className="text-[#F8F8F2] font-medium">{contact.name || 'HR Contact'}</span>
                                {contact.mx_verified && (
                                  <span className="px-2 py-1 bg-[#50FA7B] text-[#282A36] rounded text-xs font-semibold">
                                    Verified
                                  </span>
                                )}
                              </div>
                              <span className={`px-2 py-1 rounded text-xs font-semibold ${
                                contact.confidence_level === 'high' ? 'bg-[#50FA7B] text-[#282A36]' :
                                contact.confidence_level === 'medium' ? 'bg-[#FFB86C] text-[#282A36]' :
                                'bg-[#6272A4] text-[#F8F8F2]'
                              }`}>
                                {contact.confidence_level} confidence
                              </span>
                            </div>
                            <p className="text-[#8BE9FD] font-mono text-sm">{contact.email}</p>
                            {contact.title && (
                              <p className="text-[#6272A4] text-sm mt-1">{contact.title}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div>
                  <div className="bg-[#282A36] p-4 rounded-lg border border-[#6272A4] mb-4">
                    <h3 className="text-lg font-semibold text-[#F8F8F2] mb-3">Details</h3>
                    <div className="space-y-3 text-sm">
                      <div className="flex items-center gap-2">
                        <MapPin className="h-4 w-4 text-[#FF79C6]" />
                        <span className="text-[#F8F8F2]">{selectedInternship.city}, {selectedInternship.region}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getModalityColor(selectedInternship.modality)}`}>
                          {selectedInternship.modality.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <DollarSign className="h-4 w-4 text-[#50FA7B]" />
                        <span className="text-[#F8F8F2]">{formatSalary(selectedInternship.salary_min, selectedInternship.salary_max, selectedInternship.salary_currency)}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-[#FFB86C]" />
                        <span className="text-[#F8F8F2]">{selectedInternship.duration_months} months</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Briefcase className="h-4 w-4 text-[#BD93F9]" />
                        <span className="text-[#F8F8F2]">{selectedInternship.education_level}</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <a
                      href={selectedInternship.apply_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-center gap-2 w-full px-6 py-3 bg-[#50FA7B] text-[#282A36] rounded-xl hover:bg-[#5FFF8A] font-semibold transition-all"
                    >
                      <ExternalLink className="h-5 w-5" />
                      Apply Now
                    </a>
                    {selectedInternship.contact_emails.length > 0 && (
                      <button className="flex items-center gap-2 px-6 py-3 bg-[#8BE9FD] text-[#282A36] rounded-xl hover:bg-[#A4FFFF] font-semibold transition-all">
                        <Mail className="h-5 w-5" />
                        Contact HR
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
