import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    const filePath = path.join(process.cwd(), 'bills_data.json');
    const fileData = fs.readFileSync(filePath, 'utf8');
    const bills = JSON.parse(fileData);
    
    return NextResponse.json({ bills });
  } catch (error) {
    console.error('Error reading bills:', error);
    return NextResponse.json({ error: 'Failed to fetch bills' }, { status: 500 });
  }
} 