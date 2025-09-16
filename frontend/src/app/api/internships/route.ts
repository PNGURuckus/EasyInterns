import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // In a real app, this would fetch from your backend API
    // For now, we'll return some mock data
    const mockInternships = [
      {
        id: '1',
        title: 'Software Engineering Intern',
        company: 'TechCorp',
        location: 'Toronto, ON',
        city: 'Toronto',
        region: 'ON',
        is_remote: true,
        type: 'Summer 2024',
        posted_date: '2024-01-15',
        application_deadline: '2024-03-15',
        salary_range: '$25 - $35/hour',
        description: 'Join our engineering team to work on exciting projects and gain hands-on experience with modern technologies.',
        apply_url: 'https://example.com/apply/1'
      },
      {
        id: '2',
        title: 'Marketing Intern',
        company: 'DigitalAgency',
        location: 'Vancouver, BC',
        city: 'Vancouver',
        region: 'BC',
        is_remote: false,
        type: 'Winter 2024',
        posted_date: '2024-01-10',
        application_deadline: '2024-02-28',
        salary_range: '$22 - $30/hour',
        description: 'Assist our marketing team with campaigns, social media, and content creation.',
        apply_url: 'https://example.com/apply/2'
      },
      {
        id: '3',
        title: 'Data Science Intern',
        company: 'DataInsights',
        location: 'Montreal, QC',
        city: 'Montreal',
        region: 'QC',
        is_remote: true,
        type: 'Summer 2024',
        posted_date: '2024-01-20',
        application_deadline: '2024-04-01',
        salary_range: '$30 - $45/hour',
        description: 'Work with our data science team to analyze large datasets and build predictive models.',
        apply_url: 'https://example.com/apply/3'
      },
      {
        id: '4',
        title: 'UX/UI Design Intern',
        company: 'DesignHub',
        location: 'Calgary, AB',
        city: 'Calgary',
        region: 'AB',
        is_remote: true,
        type: 'Summer 2024',
        posted_date: '2024-01-18',
        application_deadline: '2024-03-20',
        salary_range: '$24 - $32/hour',
        description: 'Design beautiful and intuitive user interfaces for our clients across various industries.',
        apply_url: 'https://example.com/apply/4'
      },
      {
        id: '5',
        title: 'Business Development Intern',
        company: 'GrowthLabs',
        location: 'Ottawa, ON',
        city: 'Ottawa',
        region: 'ON',
        is_remote: false,
        type: 'Summer 2024',
        posted_date: '2024-01-22',
        application_deadline: '2024-03-10',
        salary_range: '$23 - $28/hour',
        description: 'Help identify new business opportunities and build relationships with potential clients.',
        apply_url: 'https://example.com/apply/5'
      },
      {
        id: '6',
        title: 'DevOps Engineering Intern',
        company: 'CloudScale',
        location: 'Remote',
        city: 'Remote',
        region: 'Canada',
        is_remote: true,
        type: 'Summer 2024',
        posted_date: '2024-01-25',
        application_deadline: '2024-04-15',
        salary_range: '$28 - $40/hour',
        description: 'Work with our infrastructure team to build and maintain scalable cloud solutions.',
        apply_url: 'https://example.com/apply/6'
      }
    ];

    return NextResponse.json({ items: mockInternships });
  } catch (error) {
    console.error('Error fetching internships:', error);
    return NextResponse.json(
      { error: 'Failed to fetch internships' },
      { status: 500 }
    );
  }
}
