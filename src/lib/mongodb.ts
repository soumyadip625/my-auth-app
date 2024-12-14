import { MongoClient } from 'mongodb';

const uri = process.env.MONGODB_URI || "mongodb://localhost:27017";
const options = {};

let client: MongoClient;
let clientPromise: Promise<MongoClient>;

declare global {
    var _mongoClientPromise: Promise<MongoClient>;
}

if (!global._mongoClientPromise) {
    client = new MongoClient(uri, options);
    global._mongoClientPromise = client.connect();
}
clientPromise = global._mongoClientPromise;

export async function connectToDatabase() {
    try {
        const client = await clientPromise;
        const db = client.db('email_dashboard');
        return { client, db };
    } catch (error) {
        console.error('Failed to connect to database:', error);
        throw error;
    }
} 