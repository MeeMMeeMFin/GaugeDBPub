//db = db.getSiblingDB("testDB");
db = db.getSiblingDB('results');
db.createCollection("initial");
db.initial.insertMany([
    {
        "testi":0
    }
]);

db = db.getSiblingDB('dictionary');
db.createCollection("initial");
db.initial.insertMany([
    {
        "testi":0
    }
]);


db = db.getSiblingDB('gameDatas');
db.createCollection("initial");
db.initial.insertMany([
    {
        "testi":0
    }
]);

db = db.getSiblingDB('testResults');
db.createCollection("initial");
db.initial.insertMany([
    {
        "testi":0
    }
]);

db = db.getSiblingDB('admin');
// Admin
db.createUser({
    user: process.env.MONGODB_USER1_NAME,
    pwd: process.env.MONGODB_USER1_PWD,
    roles: [
        {
            role: "read",
            db: "results"
        },
        {
            role: "read",
            db: "dictionary"
        }
    ]
});
// Preprocess
db.createUser(
    {
        user: process.env.MONGODB_USER2_NAME,
        pwd: process.env.MONGODB_USER2_PWD,
        roles: [
            {
                role: "readWrite",
                db: "dictionary"
            },
            {
                role: "readWrite",
                db: "gameDatas"
            }
        ]
    }
);
// AI
db.createUser(
    {
        user: process.env.MONGODB_USER3_NAME,
        pwd: process.env.MONGODB_USER3_PWD,
        roles: [
            {
                role: "read",
                db: "gameDatas"
            },
            {
                role: "read",
                db: "dictionary"
            },
            {
                role: "readWrite",
                db: "results"
            }
        ]
    }
);
// Human
db.createUser(
    {
        user: process.env.MONGODB_USER4_NAME,
        pwd: process.env.MONGODB_USER4_PWD,
        roles: [
            {
                role: "read",
                db: "testResults"
            }
        ]
    }
);