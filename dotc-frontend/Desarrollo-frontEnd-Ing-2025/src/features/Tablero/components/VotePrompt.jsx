import { Button } from "../../../components/Button/Button";
import { useEffect, useRef, useState } from "react";
import "./VotePrompt.css"

export function VotePrompt({ votePrompt, playSel, onSendVote, opponents = [], timeoutMs = 20000 }) {
    if (!votePrompt) return null;

    const timerRef = useRef(null);
    const [timeLeft, setTimeLeft] = useState(Math.floor(timeoutMs / 1000));

    useEffect(() => {
        setTimeLeft(Math.floor(timeoutMs / 1000));
        timerRef.current = setTimeout(() => {
            let targetId = playSel?.targetPlayerId;

            if (!targetId) {
                const candidates = Array.isArray(opponents) ? opponents : [];
                if (candidates.length > 0) {
                    console.log('candidates: ',candidates);
                    const random = candidates[Math.floor(Math.random() * candidates.length)];
                    const autoId = random?.player_id;
                    playSel.setTargetPlayerId(autoId);

                    if (autoId && playSel?.setTargetPlayerId) {
                        console.log('autoId: ', autoId);
                        setTimeout(() => onSendVote && onSendVote(), 0);
                        return;
                    }
                }
            }

            onSendVote && onSendVote();
        }, timeoutMs);

        // Intervalo para actualizar el contador
        const interval = setInterval(() => {
            setTimeLeft(prev => prev > 0 ? prev - 1 : 0);
        }, 1000);

        return () => {
            if (timerRef.current) {
                clearTimeout(timerRef.current);
                timerRef.current = null;
            }
            clearInterval(interval);
        };
    }, [votePrompt, timeoutMs]);

    const handleSendNow = () => {
        if (timerRef.current) {
            clearTimeout(timerRef.current);
            timerRef.current = null;
        }
        onSendVote && onSendVote();
    };

    return (
        <div className="vote-prompt-overlay">
            <div className="vote-prompt">
                <p>Selecciona al jugador que sospeches que sea el asesino</p>
                <div style={{ color: "#fff", marginBottom: "1rem", fontSize: "1.2rem" }}>
                    Tiempo restante: {timeLeft}s
                </div>
                <Button
                    disabled={!playSel?.targetPlayerId}
                    variant="small"
                    onClick={handleSendNow}
                >
                    Mandar sospecha
                </Button>
            </div>
        </div>
    );
}