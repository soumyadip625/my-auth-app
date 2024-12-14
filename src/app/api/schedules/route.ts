import { connectToDatabase } from '@/lib/mongodb';
import { NextResponse } from 'next/server';

export async function GET() {
    try {
        const { db } = await connectToDatabase();
        
        const schedules = await db
            .collection('schedules')
            .find({})
            .toArray();
            
        return NextResponse.json(schedules);
    } catch (error) {
        console.error('Error fetching schedules:', error);
        return NextResponse.json([]);  // Return empty array on error
    }
} 