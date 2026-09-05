// src/pages/Rules.jsx
import React from "react";
import { FaCheckCircle, FaTimesCircle, FaFire, FaBolt, FaTrophy } from "react-icons/fa";
import { motion } from "framer-motion";

const playerExamples = [
  {
    position: "QB",
    name: "Example QB",
    stats: {
      passing_yards: 320,
      passing_tds: 1,
    },
    criteriaMet: true,
    points: 1,
  },
  {
    position: "RB",
    name: "Example RB",
    stats: {
      rushing_yards: 80,
      receiving_yards: 50,
      total_tds: 0,
    },
    criteriaMet: true,
    points: 1,
  },
  {
    position: "WR",
    name: "Example WR",
    stats: {
      rushing_yards: 10,
      receiving_yards: 90,
      total_tds: 1,
    },
    criteriaMet: true,
    points: 1,
  },
];

// New examples for missed thresholds and triple streaks
const missedExamples = [
  {
    position: "QB",
    name: "Missed QB",
    stats: {
      passing_yards: 280,
      passing_tds: 1,
    },
    criteriaMet: false,
    points: 0,
  },
  {
    position: "RB",
    name: "Missed RB",
    stats: {
      rushing_yards: 50,
      receiving_yards: 40,
      total_tds: 0,
    },
    criteriaMet: false,
    points: 0,
  },
  {
    position: "WR",
    name: "Missed WR",
    stats: {
      rushing_yards: 30,
      receiving_yards: 80,
      total_tds: 0,
    },
    criteriaMet: false,
    points: 0,
  },
];

const tripleStreakExamples = [
  {
    title: "Triple Streak Met",
    description:
      "All 3 positions hit thresholds in consecutive weeks — stacking big bonus points!",
    weeks: [
      { week: 1, hit: true, bonus: "+5 pts" },
      { week: 2, hit: true, bonus: "+10 pts" },
      { week: 3, hit: true, bonus: "+15 pts" },
    ],
    met: true,
  },
  {
    title: "Triple Streak Broken",
    description:
      "Missed a week — no bonus points added that week, streak resets.",
    weeks: [
      { week: 1, hit: true, bonus: "+5 pts" },
      { week: 2, hit: false, bonus: "0 pts" },
      { week: 3, hit: true, bonus: "+5 pts" },
    ],
    met: false,
  },
];

const Rules = () => {
  return (
    <div className="max-w-4xl mx-auto p-6 bg-gray-800 rounded-xl shadow-md mt-6 text-white">
      <h2 className="text-4xl font-bold mb-6 text-yellow-400">Scoring & Rules</h2>

      <section className="mb-8">
        <h3 className="text-2xl font-semibold mb-2 text-green-300">🎯 Weekly Picks</h3>
        <ul className="list-disc ml-6 space-y-2 text-sm">
          <li>Select <strong>1 QB, 1 RB, and 1 WR</strong> each week.</li>
          <li>You earn points if your players hit their performance thresholds.</li>
          <li>You cannot pick the same player again for a position while you're on a streak for that position.</li>
          <li><FaTimesCircle className="inline text-red-400" /> If any player fails, the respective positional streak resets!</li>
        </ul>
      </section>

      <section className="mb-8">
        <h3 className="text-2xl font-semibold mb-2 text-blue-300">📊 Scoring Criteria</h3>
        <div className="space-y-3 text-sm">
          <div>
            <span className="font-bold text-yellow-200">Quarterback (QB)</span>:
            <ul className="list-disc ml-6">
              <li>300+ passing yards OR 2+ TDs (passing, rushing, receiving)</li>
              <li>OR 100+ total rushing (or 125+ total rushing + receiving yards)</li>
            </ul>
          </div>
          <div>
            <span className="font-bold text-yellow-200">Running Back (RB) / Wide Receiver (WR)</span>:
            <ul className="list-disc ml-6">
              <li>100+ rushing OR 100+ receiving yards</li>
              <li>OR 125+ total rushing + receiving yards</li>
              <li>OR 1+ total touchdowns (rushing or receiving or passing)</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="mb-8">
        <h3 className="text-2xl font-semibold mb-2 text-pink-300">🔥 Positional Streak Bonuses</h3>
        <p className="text-sm mb-2">
          Each time a position hits the threshold in consecutive weeks, your streak grows and adds bonus points:
        </p>
        <ul className="list-disc ml-6 text-sm space-y-1">
          <li><FaFire className="inline text-orange-400" /> Week 1 hit: +1 point</li>
          <li><FaFire className="inline text-orange-400" /> Week 2 hit: +2 points</li>
          <li><FaFire className="inline text-orange-400" /> Week 3 hit: +3 points, and so on...</li>
        </ul>
      </section>

      <section className="mb-8">
        <h3 className="text-2xl font-semibold mb-2 text-purple-300">🏆 All-Position Bonus</h3>
        <p className="text-sm mb-2">
          Hit on <strong>all 3 positions in a single week</strong> to earn a major bonus:
        </p>
        <ul className="list-disc ml-6 text-sm">
          <li>Week 1: +5 bonus</li>
          <li>Week 2 in a row: +10 bonus</li>
          <li>Week 3 in a row: +15 bonus</li>
          <li>...and it keeps stacking!</li>
        </ul>
      </section>

      {/* Existing Scoring Examples */}
      <motion.section
        className="mb-8"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3, duration: 0.7 }}
      >
        <h3 className="text-2xl font-semibold mb-4 text-teal-300 flex items-center gap-2">
          <FaBolt className="text-yellow-400" />
          Scoring Examples
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-6">
          {playerExamples.map(({ position, name, stats, criteriaMet, points }, idx) => (
            <motion.div
              key={idx}
              className={`p-4 rounded-lg border ${criteriaMet ? "border-green-400 bg-green-900/30" : "border-red-600 bg-red-900/30"
                } shadow-lg`}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2 * idx }}
            >
              <h4 className="text-lg font-bold mb-2">
                {position} - {name}
              </h4>
              <ul className="text-sm space-y-1">
                {position === "QB" && (
                  <>
                    <li>Passing Yards: {stats.passing_yards}</li>
                    <li>Passing TDs: {stats.passing_tds}</li>
                    <li>
                      {criteriaMet ? (
                        <span className="text-green-400 font-semibold flex items-center gap-1">
                          <FaCheckCircle /> Hits QB threshold! +{points} pt
                        </span>
                      ) : (
                        <span className="text-red-500 font-semibold flex items-center gap-1">
                          <FaTimesCircle /> Does not hit threshold
                        </span>
                      )}
                    </li>
                  </>
                )}
                {(position === "RB" || position === "WR") && (
                  <>
                    <li>Rushing Yards: {stats.rushing_yards}</li>
                    <li>Receiving Yards: {stats.receiving_yards}</li>
                    <li>Total Touchdowns: {stats.total_tds}</li>
                    <li>
                      {criteriaMet ? (
                        <span className="text-green-400 font-semibold flex items-center gap-1">
                          <FaCheckCircle /> Hits RB/WR threshold! +{points} pt
                        </span>
                      ) : (
                        <span className="text-red-500 font-semibold flex items-center gap-1">
                          <FaTimesCircle /> Does not hit threshold
                        </span>
                      )}
                    </li>
                  </>
                )}
              </ul>
            </motion.div>
          ))}
        </div>

        {/* New Missed Threshold Examples */}
        <h4 className="text-xl font-semibold mb-3 text-red-400">Missed Thresholds</h4>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-6">
          {missedExamples.map(({ position, name, stats, criteriaMet }, idx) => (
            <motion.div
              key={idx}
              className={`p-4 rounded-lg border ${criteriaMet ? "border-green-400 bg-green-900/30" : "border-red-600 bg-red-900/30"
                } shadow-lg`}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2 * idx }}
            >
              <h4 className="text-lg font-bold mb-2">
                {position} - {name}
              </h4>
              <ul className="text-sm space-y-1">
                {position === "QB" && (
                  <>
                    <li>Passing Yards: {stats.passing_yards}</li>
                    <li>Passing TDs: {stats.passing_tds}</li>
                    <li>
                      <span className="text-red-500 font-semibold flex items-center gap-1">
                        <FaTimesCircle /> Does not hit threshold
                      </span>
                    </li>
                  </>
                )}
                {(position === "RB" || position === "WR") && (
                  <>
                    <li>Rushing Yards: {stats.rushing_yards}</li>
                    <li>Receiving Yards: {stats.receiving_yards}</li>
                    <li>Total Touchdowns: {stats.total_tds}</li>
                    <li>
                      <span className="text-red-500 font-semibold flex items-center gap-1">
                        <FaTimesCircle /> Does not hit threshold
                      </span>
                    </li>
                  </>
                )}
              </ul>
            </motion.div>
          ))}
        </div>

        {/* Triple Streak Examples */}
        <h4 className="text-xl font-semibold mb-3 text-yellow-400">Triple Streak Examples</h4>
        <div className="space-y-6">
          {tripleStreakExamples.map(({ title, description, weeks, met }, idx) => (
            <motion.div
              key={idx}
              className={`p-4 rounded-lg border ${met ? "border-green-400 bg-green-900/30" : "border-red-600 bg-red-900/30"
                } shadow-lg`}
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3 * idx }}
            >
              <h5 className="text-lg font-bold mb-2 flex items-center gap-2">
                {title}{" "}
                {met ? (
                  <FaCheckCircle className="text-green-400" />
                ) : (
                  <FaTimesCircle className="text-red-500" />
                )}
              </h5>
              <p className="mb-3 text-sm">{description}</p>
              <table className="w-full text-sm border-collapse border border-gray-600">
                <thead>
                  <tr className="bg-gray-700">
                    <th className="border border-gray-600 p-1 text-center">Week</th>
                    <th className="border border-gray-600 p-1 text-center">Hit Threshold</th>
                    <th className="border border-gray-600 p-1 text-center">Bonus Points</th>
                  </tr>
                </thead>
                <tbody>
                  {weeks.map(({ week, hit, bonus }) => (
                    <tr
                      key={week}
                      className={`text-center ${hit ? "bg-green-800" : "bg-red-800"
                        }`}
                    >
                      <td className="border border-gray-600 p-1">{week}</td>
                      <td className="border border-gray-600 p-1 flex justify-center items-center gap-1">
                        {hit ? (
                          <FaCheckCircle className="text-green-400" />
                        ) : (
                          <FaTimesCircle className="text-red-400" />
                        )}
                      </td>
                      <td className="border border-gray-600 p-1">{bonus}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </motion.div>
          ))}
        </div>
      </motion.section>

      <section>
        <h3 className="text-2xl font-semibold mb-2 text-gray-300">🧠 Strategy Tips</h3>
        <ul className="list-disc ml-6 text-sm space-y-1">
          <li>Watch for injuries and matchup difficulty when making your picks.</li>
          <li>Target consistent volume players over boom/bust types for long streaks.</li>
          <li>You can modify player picks up until respective game time start, choose wisely!</li>
        </ul>
      </section>
    </div>
  );
};

export default Rules;
