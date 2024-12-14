import { NextResponse } from 'next/server';
import { MongoClient } from 'mongodb';

const MONGO_URI = "mongodb://localhost:27017";
const DATABASE_NAME = "email_dashboard";
const COLLECTION_NAME = "emails";

export async function GET() {
    try {
        // Connect to the MongoDB database
        const client = await MongoClient.connect(MONGO_URI);
        const db = client.db(DATABASE_NAME);
        const collection = db.collection(COLLECTION_NAME);

        // Fetch email summaries with categories
        const emails = await collection.find({}, { projection: { summary: 1, subject: 1, category: 1 } }).toArray();

        // Close the database connection
        client.close();

        return NextResponse.json(emails);
    } catch (error) {
        console.error('Error fetching email summaries:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
