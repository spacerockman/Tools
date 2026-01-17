import { Button } from "./ui/button";
import { Dumbbell, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";

export default function TrainingSuggestions({ suggestions }) {
    const router = useRouter();

    const handleTrain = (point) => {
        // Generate quiz specifically for this point
        // We can use the existing generate flow, or a specific "train weak point" flow
        // For now, let's treat it as a topic generation
        localStorage.removeItem('currentQuestions'); // Clear previous
        // Redirect to home with pre-filled topic? Or direct API call?
        // Let's do direct API call shim or navigate to home with query param (simpler for now if we don't want to duplicate logic)
        // Actually, let's just trigger generation in logic if possible, or tell user to type it.
        // Better: Navigate to home and auto-fill input via query param?
        // Simplest: Just Copy to clipboard or set state. 
        // Let's try to navigate to home with a prompt.
        // But since the user wants "Click to train", let's assume we can pass it to the generator.

        // We'll output a recommended topic to copy for now, or just handle it if page.js supports query params.
        // Let's just create a quick direct link logic.
        const encoded = encodeURIComponent(point);
        router.push(`/?topic=${encoded}&auto=true`);
    };

    if (!suggestions || suggestions.length === 0) return null;

    return (
        <div className="space-y-4">
            <h3 className="font-bold text-xl flex items-center gap-2">
                <Dumbbell className="w-5 h-5 text-indigo-500" />
                Recommended Training
            </h3>
            <div className="grid grid-cols-1 gap-3">
                {suggestions.map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between p-4 bg-card border rounded-lg hover:bg-accent/50 transition">
                        <div className="flex-1">
                            <div className="font-medium">{item.point}</div>
                            <div className="text-xs text-muted-foreground line-clamp-1">{item.description}</div>
                        </div>
                        <Button
                            size="sm"
                            variant="outline"
                            className="ml-4 gap-1"
                            onClick={() => handleTrain(item.point)}
                        >
                            Train 10 <ArrowRight className="w-3 h-3" />
                        </Button>
                    </div>
                ))}
            </div>
        </div>
    );
}
