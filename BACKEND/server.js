// server.js
import express from "express";
import mongoose from "mongoose";
import bodyParser from "body-parser";
import cors from "cors";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import multer from "multer";

const app = express();
app.use(cors());
app.use(bodyParser.json());

// ===== MongoDB Connection =====
mongoose.connect("mongodb://127.0.0.1:27017/spinalTumorDB", {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});
const db = mongoose.connection;
db.on("error", console.error.bind(console, "MongoDB connection error:"));
db.once("open", () => console.log("✅ Connected to MongoDB"));

// ===== Schemas =====
const userSchema = new mongoose.Schema({
  name: { type: String, required: true },
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
});

const predictionSchema = new mongoose.Schema({
  userId: String,
  filename: String,
  result: String,
  confidence: String,
  date: { type: Date, default: Date.now },
});

const chatSchema = new mongoose.Schema({
  userId: { type: String, required: true },
  question: String,
  answer: String,
  timestamp: { type: Date, default: Date.now },
});

const User = mongoose.model("User", userSchema);
const Prediction = mongoose.model("Prediction", predictionSchema);
const Chat = mongoose.model("Chat", chatSchema);

// ===== Middleware =====
const SECRET_KEY = "supersecretkey"; // change in production

function authMiddleware(req, res, next) {
  const authHeader = req.headers["authorization"];
  if (!authHeader) return res.status(401).json({ msg: "No token provided" });

  const token = authHeader.split(" ")[1];
  if (!token) return res.status(401).json({ msg: "Invalid token format" });

  try {
    const decoded = jwt.verify(token, SECRET_KEY);
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(401).json({ msg: "Token has expired" });
  }
}

// ===== Auth Endpoints =====
app.post("/api/auth/register", async (req, res) => {
  try {
    const { name, email, password } = req.body;
    if (!name || !email || !password)
      return res.status(400).json({ msg: "All fields required" });

    const existingUser = await User.findOne({ email });
    if (existingUser) return res.status(400).json({ msg: "User already exists" });

    const hashedPassword = await bcrypt.hash(password, 10);
    const user = new User({ name, email, password: hashedPassword });
    await user.save();

    res.json({ msg: "Registration successful" });
  } catch (err) {
    console.error(err);
    res.status(500).json({ msg: "Server error" });
  }
});

app.post("/api/auth/login", async (req, res) => {
  try {
    const { email, password } = req.body;
    const user = await User.findOne({ email });
    if (!user) return res.status(400).json({ msg: "Invalid credentials" });

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return res.status(400).json({ msg: "Invalid credentials" });

    const token = jwt.sign(
      { id: user._id, name: user.name, email: user.email },
      SECRET_KEY,
      { expiresIn: "1h" }
    );

    res.json({ token, user: { name: user.name, email: user.email } });
  } catch (err) {
    console.error(err);
    res.status(500).json({ msg: "Server error" });
  }
});

// ===== Prediction Endpoints =====
const storage = multer.memoryStorage();
const upload = multer({ storage });

function simulatePrediction() {
  const result = Math.random() > 0.5 ? "Tumor Detected" : "No Tumor";
  const confidence = (Math.random() * (99 - 80) + 80).toFixed(2) + "%";
  return { result, confidence };
}

app.post("/api/predict/upload", authMiddleware, upload.single("mriScan"), async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ msg: "No file uploaded" });

    const { result, confidence } = simulatePrediction();
    const prediction = new Prediction({
      userId: req.user.id,
      filename: req.file.originalname,
      result,
      confidence,
    });
    await prediction.save();

    res.json({ prediction });
  } catch (err) {
    console.error(err);
    res.status(500).json({ msg: "Prediction failed" });
  }
});

app.get("/api/predict/stats", authMiddleware, async (req, res) => {
  try {
    const userId = req.user.id;
    const recent_predictions = await Prediction.find({ userId }).sort({ date: -1 }).limit(5);

    const tumorCount = await Prediction.countDocuments({ userId, result: "Tumor Detected" });
    const noTumorCount = await Prediction.countDocuments({ userId, result: "No Tumor" });

    res.json({
      recent_predictions: recent_predictions.map(p => ({
        date: p.date.toLocaleString(),
        filename: p.filename,
        result: p.result,
        confidence: p.confidence,
      })),
      total_counts: { tumor: tumorCount, no_tumor: noTumorCount },
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ msg: "Could not fetch stats" });
  }
});

// ===== Chatbot Endpoints =====
app.post("/api/chatbot/ask", async (req, res) => {
  try {
    const { userId, question } = req.body;
    const answer = `This is a dummy answer for: "${question}"`; // replace later
    const chat = new Chat({ userId, question, answer });
    await chat.save();
    res.json({ answer });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Server error" });
  }
});

app.get("/api/user/chat-history/:userId", async (req, res) => {
  try {
    const { userId } = req.params;
    const history = await Chat.find({ userId }).sort({ timestamp: -1 });
    res.json(history);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Server error" });
  }
});

// ===== Start Server =====
const PORT = 5000;
app.listen(PORT, () => console.log(`🚀 Server running on http://localhost:${PORT}`));
