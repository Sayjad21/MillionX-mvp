# MillionX Frontend Testing Checklist 🧪

**Test Environment:** `http://localhost:5173`  
**API Backend:** `http://localhost:8000`

---

## ✅ Feature 1: Product Images & Expanded Cards

### Test Steps:

1. Open dashboard (skip onboarding if shown)
2. Look at product cards in grid

### Expected Results:

- ✅ Each card shows product image at top (phones, laptops, etc.)
- ✅ Product name overlays image with gradient
- ✅ Hover effect: image scales up slightly
- ✅ Colored badge (🚨 URGENT / ⚠️ RESTOCK / ✅ STABLE)

### Test Interaction:

1. **Click any product card**
2. Modal expands with full details

### Expected Modal Content:

- ✅ Product name, ID, recommendation
- ✅ 7-day forecast number
- ✅ Close button (X) works

---

## 📈 Feature 2: Live Pulse Graph (LineChart)

### Test Steps:

1. Click any product card to open modal
2. Scroll down in the modal

### Expected Results:

- ✅ Section titled **"📈 Live Demand Pulse"**
- ✅ Green line chart showing demand predictions
- ✅ X-axis: Dates (e.g., "24 Dec", "25 Dec")
- ✅ Y-axis: Quantity numbers
- ✅ Hover over line: tooltip shows date + quantity
- ✅ Green dots on data points

### If Graph Missing:

- Check console for errors
- Verify product has `forecast.predictions` array in API response

---

## 🧠 Feature 3: XAI "Why?" Tooltip (Model Metrics)

### Test Steps:

1. Open product modal (click any card)
2. Find **"🎯 Model Confidence"** section
3. Hover over **question mark icon (?)** on the right

### Expected Tooltip Content:

```
🧠 Why This Prediction?

Model Accuracy (R²): 87.5%
Trend Slope: 📈 2.34
Training Data: 30 days

Overall Confidence: 85%

AI model trained on historical sales data using linear regression
```

### Expected Behavior:

- ✅ Tooltip appears on hover
- ✅ Shows R², slope, training days
- ✅ Disappears when mouse leaves

---

## 🚫 Feature 4: Report Fraud Button (COD Shield)

### Test Steps:

1. Look at right sidebar: **COD Shield** panel
2. Enter phone number: `+8801712345678`
3. Click **"Analyze Risk"**
4. Wait for result (radar animation)
5. Scroll down to see **"🚫 Report as Fraud"** red button
6. Click the button

### Expected Results:

**Before Click:**

- ✅ Red button: "🚫 Report as Fraud"
- ✅ Shows risk score (0-100)
- ✅ Risk level (LOW/MEDIUM/HIGH)

**After Click:**

- ✅ Button changes to success message
- ✅ Shows: **"🚫 Number Added to National Blacklist"**
- ✅ Green success box with text: "This phone number is now flagged across all merchants"
- ✅ Button disabled (no double-reporting)

**Test Again:**

- Enter SAME phone number
- Click Analyze Risk again
- Risk score should be HIGHER (blacklist hit detected)

---

## 🎙️ Feature 5: Voice Commands (Bhai-Bot)

### Test Steps:

1. Click green **floating microphone button** (bottom-right)
2. Chat window opens
3. Click **microphone icon** in input field (turns red when listening)
4. **Speak clearly:** "Show urgent stock"

### Expected Results:

**On Click Microphone:**

- ✅ Button turns RED and pulses
- ✅ Message appears: "🎙️ Listening... Speak now!"

**After Speaking:**

- ✅ Your speech transcribed as user message
- ✅ Bot responds: "🚨 Filtering for URGENT stock alerts..."
- ✅ Dashboard filters to show only URGENT products

### Test Commands:

| **Say This**         | **Bot Should Do**                               |
| -------------------- | ----------------------------------------------- |
| "Show urgent stock"  | Filter dashboard for 🚨 URGENT items            |
| "Check forecast"     | Show all products                               |
| "What's the profit?" | Reply: "💰 Your projected profit is ৳45,000..." |
| "Stable items"       | Filter for ✅ STABLE products                   |
| "Hello"              | Reply: "🤖 Walaikum Assalam! How can I help?"   |

### Fallback Test (Text):

- Type same commands in text box
- Press Enter or click Send
- Should work identically

### Browser Compatibility:

- ✅ Works: Chrome, Edge, Safari (desktop)
- ❌ Not supported: Firefox (shows error message)

---

## 🛡️ Feature 6: COD Risk Checker (Fixed API)

### Test Steps:

1. Open COD Shield panel (right sidebar)
2. Enter phone: `+8801798765432`
3. Click **"Analyze Risk"**

### Expected Results:

**Loading State:**

- ✅ Button shows "Scanning..."
- ✅ Radar sweep animation (3 concentric circles)
- ✅ Shield icon pulses

**Success State:**

- ✅ Risk score appears (0-100)
- ✅ Risk level badge (LOW = green, MEDIUM = yellow, HIGH = orange)
- ✅ Recommendation text
- ✅ Risk factors list (if any)

**OLD BUG (Now Fixed):**

- ❌ ~~Used to show: "0 Risk Score, MODERATE RISK, Recommendation: RETRY"~~
- ✅ **Now shows real scores** like: "45 Risk Score, MEDIUM, Call customer to confirm"

### Test Different Numbers:

```
+8801712345678  → Should be LOW risk (new number)
+8801798765432  → Test with this, then report fraud
(same number)   → Re-test, should be HIGH risk now
```

---

## 🎨 Feature 7: All Products Display (Updated)

### Test Steps:

1. Load dashboard
2. Count visible product cards

### Expected Results:

- ✅ Shows **46 unique products** (up from 30)
- ✅ New categories visible:
  - 🎮 Gaming: PS5, Xbox, Nintendo Switch
  - ⌚ Wearables: Apple Watch, Fitbit, Garmin
  - 📱 Tablets: iPad, Galaxy Tab, Surface
- ✅ Grid layout: 3 columns on desktop
- ✅ Responsive: 1 column on mobile

---

## 🔍 Integration Test (Full Flow)

### Scenario: Merchant checks risky order

1. **Open Dashboard** → See 46 products with images ✅
2. **Click "iPhone 15 Pro Max"** → Modal opens ✅
3. **View LineChart** → See 7-day demand pulse ✅
4. **Hover "?" icon** → XAI tooltip shows model accuracy ✅
5. **Close modal** → Return to dashboard ✅
6. **Click Bhai-Bot** → Chat opens ✅
7. **Say "urgent"** → Dashboard filters to urgent items ✅
8. **Open COD Shield** → Panel ready ✅
9. **Enter phone: +8801712345678** → Click Analyze ✅
10. **Result: HIGH risk** → Click "Report Fraud" ✅
11. **Success message** → Number blacklisted ✅
12. **Test same number again** → Risk score increases ✅

---

## 🐛 Known Issues / Edge Cases

### Issue 1: Voice not working

- **Cause:** Browser doesn't support Web Speech API
- **Fix:** Use Chrome/Edge, or type commands instead

### Issue 2: No products showing

- **Check:** Is backend running? `docker ps` should show `millionx-fastapi`
- **Fix:** `docker-compose restart fastapi`

### Issue 3: Graph not rendering

- **Check:** Does product have `forecast.predictions` array?
- **Fix:** Run `python check_db.py` to verify 150 sales records exist

### Issue 4: Images not loading

- **Cause:** Unsplash CDN down (rare)
- **Fallback:** Default tech image shows

---

## ✅ Quick Smoke Test (2 minutes)

**Minimum viable demo check:**

```bash
# 1. Backend running?
curl http://localhost:8000/health

# 2. Frontend running?
# Open http://localhost:5173

# 3. Quick clicks:
- Click any product → Modal with graph? ✅
- Hover (?) icon → Tooltip appears? ✅
- Click Bhai-Bot → Chat opens? ✅
- Say/type "urgent" → Dashboard filters? ✅
- COD Shield → Enter phone → Risk score? ✅
- Click Report Fraud → Success message? ✅
```

**If all ✅ → Demo ready! 🚀**

---

## 📊 Expected Performance

- **Dashboard load:** < 2 seconds (46 products)
- **Modal open:** Instant (Framer Motion)
- **Voice recognition:** 1-3 seconds (browser dependent)
- **Risk analysis:** < 1 second (FastAPI)
- **Graph render:** < 500ms (Recharts)

---

## 🎥 Demo Script (60 seconds)

**"Let me show you MillionX AI..."**

1. **"Here's our dashboard"** → Scroll through 46 products with images
2. **"Click iPhone"** → Modal opens, "See the 7-day demand pulse graph"
3. **"Hover here"** → "AI shows 87% accuracy using 30 days of data"
4. **"Now voice control"** → Say "urgent" → "Dashboard filters instantly"
5. **"COD fraud detection"** → Enter phone → "High risk detected"
6. **"Report to national blacklist"** → Click → "Number flagged!"
7. **"Test again"** → Same number → "Risk score increased!"

**💥 Mic drop moment:** "Voice-first, AI-powered, fraud-protected commerce for Bangladesh's next billion users."

---

## 📝 Testing Notes

- Test on **Chrome** for best experience (voice + performance)
- Clear browser cache if seeing old data
- Check console (F12) for any API errors
- Mobile: Test on actual device, not just DevTools

**Happy Testing! 🎉**
