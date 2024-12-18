import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const response = await fetch('http://localhost:5000/api/emails');
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching emails:', error);
    return NextResponse.json(
      { error: 'Failed to fetch email summaries' },
      { status: 500 }
    );
  }
} 