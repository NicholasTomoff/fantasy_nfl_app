import React from "react";

// Match the same fallback banners used in leagues
const DEFAULT_BANNERS = [
    "https://images.pexels.com/photos/7005488/pexels-photo-7005488.jpeg",
    "https://images.pexels.com/photos/7005503/pexels-photo-7005503.jpeg",
    "https://images.pexels.com/photos/923191/pexels-photo-923191.jpeg",
];

const Banner = ({ title, subtitle, banner, index = 0 }) => {
    const fallbackBanner = DEFAULT_BANNERS[index % DEFAULT_BANNERS.length];
    const bannerUrl = banner || fallbackBanner;

    return (
        <div className="w-full mb-6">
            {/* Banner Image */}
            <div className="relative w-full h-48 rounded-lg overflow-hidden shadow-md">
                <img
                    src={bannerUrl}
                    alt={`${title} banner`}
                    className="w-full h-full object-cover brightness-75"
                    loading="lazy"
                    onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = fallbackBanner;
                    }}
                />
            </div>

            {/* Blue Info Box */}
            <div className="bg-blue-600 text-white p-6 rounded-lg mt-4 shadow-md">
                <h1 className="text-3xl font-bold">{title}</h1>
                {subtitle && <p className="mt-1 text-sm opacity-80">{subtitle}</p>}
            </div>
        </div>
    );
};

export default Banner;
