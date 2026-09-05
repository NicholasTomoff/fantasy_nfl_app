import React, { useState, useEffect } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { apiFetch } from "@/services/api";
import { useLeague } from "@/context/LeagueContext";
import { useSeason } from "@/context/SeasonContext";

const AdminLeagueFinancePage = () => {
    const { activeLeagueId } = useLeague();
    const { season } = useSeason();
    const [finance, setFinance] = useState(null);
    const [entryFee, setEntryFee] = useState("");
    const [payouts, setPayouts] = useState([]);
    const [loading, setLoading] = useState(true);

    // Fetch finance data for league + season
    const fetchFinance = async () => {
        if (!activeLeagueId || !season) return;
        setLoading(true);
        try {
            const res = await apiFetch(
                `/api/leagues/${activeLeagueId}/season/${season}/finance`
            );
            if (!res.ok) throw new Error("Failed to fetch league finance");
            const data = await res.json();
            setFinance(data);
            setEntryFee(data.entry_fee || "");
            // Convert payouts object to array of {place, amount}
            const payoutArray = Object.entries(data.payouts || {}).map(
                ([place, amount]) => ({ place: Number(place), amount })
            );
            setPayouts(payoutArray);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchFinance();
    }, [activeLeagueId, season]);

    // Save entry fee
    const handleEntryFeeSave = async () => {
        const res = await apiFetch(
            `/api/leagues/${activeLeagueId}/season/${season}/finance/entry_fee`,
            {
                method: "POST",
                body: JSON.stringify({ entry_fee: Number(entryFee) }),
            }
        );
        if (res.ok) fetchFinance();
    };

    // Toggle payment / mark paid
    const handlePaymentToggle = async (member, date = null) => {
        const res = await apiFetch(
            `/api/leagues/${activeLeagueId}/season/${season}/member/${member.user_id}/payment`,
            {
                method: "POST",
                body: JSON.stringify({
                    paid: !member.paid,
                    paid_date: date,
                }),
            }
        );
        if (res.ok) fetchFinance();
    };

    // Update payouts array in state
    const handlePayoutChange = (index, key, value) => {
        const updated = [...payouts];
        updated[index][key] = Number(value);
        setPayouts(updated);
    };

    // Add new payout row
    const handleAddPayout = () => {
        setPayouts([...payouts, { place: payouts.length + 1, amount: 0 }]);
    };

    // Delete payout row
    const handleDeletePayout = (index) => {
        setPayouts(payouts.filter((_, i) => i !== index));
    };

    // Save payouts
    const handlePayoutSave = async () => {
        // Convert array back to object for backend
        const payload = {};
        payouts.forEach((p) => {
            payload[p.place] = p.amount;
        });

        const res = await apiFetch(
            `/api/leagues/${activeLeagueId}/season/${season}/finance/payouts`,
            {
                method: "POST",
                body: JSON.stringify({ payouts: payload }),
            }
        );
        if (res.ok) fetchFinance();
    };

    if (loading || !finance) return <div>Loading...</div>;

    return (
        <div className="p-4 max-w-4xl mx-auto">
            <h1 className="text-xl font-bold mb-4">
                League Finances - Season {season}
            </h1>

            {/* Entry Fee */}
            <div className="flex items-center mb-4 gap-2">
                <label className="font-semibold">Entry Fee: $</label>
                <input
                    type="number"
                    className="border rounded px-2 py-1 w-24 text-white bg-gray-900"
                    value={entryFee}
                    onChange={(e) => setEntryFee(e.target.value)}
                />
                <button
                    onClick={handleEntryFeeSave}
                    className="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600"
                >
                    Save
                </button>
            </div>

            {/* Total Pot */}
            <div className="mb-4 font-semibold">
                Total Pot: ${finance.total_pot.toFixed(2)}
            </div>

            {/* Member Payments Table */}
            <div className="overflow-x-auto mb-6">
                <table className="w-full table-auto border-collapse border border-gray-700">
                    <thead>
                        <tr className="bg-gray-800">
                            <th className="border border-gray-600 px-2 py-1 text-left">User</th>
                            <th className="border border-gray-600 px-2 py-1">Paid</th>
                            <th className="border border-gray-600 px-2 py-1">Paid Date</th>
                            <th className="border border-gray-600 px-2 py-1">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {finance.member_payments.map((member) => (
                            <tr key={member.user_id} className="hover:bg-gray-700">
                                <td className="border border-gray-600 px-2 py-1">{member.user_name}</td>
                                <td className="border border-gray-600 px-2 py-1 text-center">
                                    {member.paid ? "✅" : "❌"}
                                </td>
                                <td className="border border-gray-600 px-2 py-1 text-center">
                                    {member.paid_date
                                        ? new Date(member.paid_date).toLocaleDateString()
                                        : "-"}
                                </td>
                                <td className="border border-gray-600 px-2 py-1 text-center">
                                    {!member.paid ? (
                                        <DatePicker
                                            selected={
                                                member.paid_date ? new Date(member.paid_date) : null
                                            }
                                            onChange={(date) =>
                                                handlePaymentToggle(member, date)
                                            }
                                            placeholderText="Mark Paid"
                                            className="text-black rounded px-2 py-1"
                                        />
                                    ) : (
                                        <button
                                            className="bg-red-500 px-2 py-1 text-white rounded hover:bg-red-600"
                                            onClick={() => handlePaymentToggle(member, null)}
                                        >
                                            Unmark
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Payouts */}
            <div className="mt-6">
                <h2 className="font-semibold mb-2">Payouts</h2>
                <table className="w-full table-auto border border-gray-600 mb-2">
                    <thead>
                        <tr className="bg-gray-800 text-white">
                            <th className="border px-2 py-1">Place</th>
                            <th className="border px-2 py-1">Amount</th>
                            <th className="border px-2 py-1">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {payouts.map((p, index) => (
                            <tr key={index} className="hover:bg-gray-700">
                                <td className="border px-2 py-1">
                                    <input
                                        type="number"
                                        value={p.place}
                                        onChange={(e) =>
                                            handlePayoutChange(index, "place", e.target.value)
                                        }
                                        className="w-16 text-white"
                                    />
                                </td>
                                <td className="border px-2 py-1">
                                    <input
                                        type="number"
                                        value={p.amount}
                                        onChange={(e) =>
                                            handlePayoutChange(index, "amount", e.target.value)
                                        }
                                        className="w-20 text-white"
                                    />
                                </td>
                                <td className="border px-2 py-1 text-center">
                                    <button
                                        className="bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600"
                                        onClick={() => handleDeletePayout(index)}
                                    >
                                        Delete
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                <button
                    className="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600 mb-2"
                    onClick={handleAddPayout}
                >
                    Add Payout
                </button>
                <br />
                <button
                    className="bg-blue-500 text-white px-4 py-1 rounded hover:bg-blue-600"
                    onClick={handlePayoutSave}
                >
                    Save Payouts
                </button>
            </div>
        </div>
    );
};

export default AdminLeagueFinancePage;
