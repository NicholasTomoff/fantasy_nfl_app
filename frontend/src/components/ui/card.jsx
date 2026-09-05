// frontend/src/components/ui/card.jsx
import * as React from "react";
import { cn } from "@/lib/utils";

const Card = React.forwardRef(({ className, children, ...props }, ref) => {
    return (
        <div
            ref={ref}
            className={cn(
                "rounded-lg border border-gray-300 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800",
                className
            )}
            {...props}
        >
            {children}
        </div>
    );
});
Card.displayName = "Card";

const CardContent = React.forwardRef(({ className, children, ...props }, ref) => {
    return (
        <div
            ref={ref}
            className={cn("p-4", className)}
            {...props}
        >
            {children}
        </div>
    );
});
CardContent.displayName = "CardContent";

export { Card, CardContent };
