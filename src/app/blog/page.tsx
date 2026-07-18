/* ================================================================
   Ev2Ev — Blog Page
   Travel blogs, charging guides, and EV trip reports
   ================================================================ */

"use client";

import Link from "next/link";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import { useI18n } from "@/lib/i18n";
import {
  BookOpen, Calendar, Eye, Heart, User, ChevronRight,
  MapPin, Zap, ArrowRight, PenSquare
} from "lucide-react";

const sampleBlogs = [
  {
    slug: "hyderabad-to-vizag-mg-windsor",
    title: "Hyderabad to Vizag in an MG Windsor EV — Complete Charging Guide",
    excerpt: "A 620km road trip with 2 charging stops. Route, costs, charger reviews, and tips for first-time EV highway travelers.",
    coverImage: "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=600&h=340&fit=crop",
    author: { name: "Rahul Sharma", avatar: "R" },
    date: "July 15, 2025",
    readTime: "8 min read",
    views: 2340,
    likes: 189,
    tags: ["Road Trip", "Hyderabad", "Vizag", "Highway", "MG Windsor"],
  },
  {
    slug: "best-ev-chargers-bangalore",
    title: "Top 15 EV Charging Stations in Bangalore — Ranked & Reviewed",
    excerpt: "We tested every major charging station in Bangalore. Here's our definitive guide with ratings, wait times, and nearby amenities.",
    coverImage: "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=600&h=340&fit=crop",
    author: { name: "Priya Menon", avatar: "P" },
    date: "July 10, 2025",
    readTime: "12 min read",
    views: 4560,
    likes: 312,
    tags: ["Bangalore", "City Guide", "Reviews"],
  },
  {
    slug: "mumbai-pune-expressway-ev-guide",
    title: "EV Charging on Mumbai-Pune Expressway — Everything You Need to Know",
    excerpt: "Complete guide to charging on India's busiest expressway. Station locations, power levels, pricing, and pro tips.",
    coverImage: "https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?w=600&h=340&fit=crop",
    author: { name: "Amit Patel", avatar: "A" },
    date: "July 5, 2025",
    readTime: "6 min read",
    views: 3210,
    likes: 245,
    tags: ["Highway", "Mumbai", "Pune", "Expressway"],
  },
  {
    slug: "cheapest-ev-charging-india",
    title: "Cheapest EV Charging in India — Operator Price Comparison 2025",
    excerpt: "We compared per-kWh prices across all major operators. Find out who offers the best value for your electric vehicle.",
    coverImage: "https://images.unsplash.com/photo-1554744512-d6c603f27c54?w=600&h=340&fit=crop",
    author: { name: "Suresh Kumar", avatar: "S" },
    date: "June 28, 2025",
    readTime: "10 min read",
    views: 5670,
    likes: 423,
    tags: ["Price Comparison", "Guide", "Tips"],
  },
  {
    slug: "tata-nexon-ev-long-range-review",
    title: "Tata Nexon EV Long Range — 6 Month Ownership Review",
    excerpt: "Real-world range, charging experience, and total cost of ownership after 15,000 km of daily driving and road trips.",
    coverImage: "https://images.unsplash.com/photo-1560958089-b8a1929cea89?w=600&h=340&fit=crop",
    author: { name: "Vikram Singh", avatar: "V" },
    date: "June 20, 2025",
    readTime: "15 min read",
    views: 8920,
    likes: 567,
    tags: ["Vehicle Review", "Tata Nexon", "Ownership"],
  },
  {
    slug: "delhi-to-jaipur-ev-trip",
    title: "Delhi to Jaipur EV Road Trip — NH-48 Charging Guide",
    excerpt: "A weekend trip covering 280km with charging stops at Neemrana. Perfect for first-time EV road trippers.",
    coverImage: "https://images.unsplash.com/photo-1477587458883-47145ed94245?w=600&h=340&fit=crop",
    author: { name: "Neha Gupta", avatar: "N" },
    date: "June 15, 2025",
    readTime: "7 min read",
    views: 3450,
    likes: 198,
    tags: ["Road Trip", "Delhi", "Jaipur", "Weekend"],
  },
];

export default function BlogPage() {
  const { t } = useI18n();

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1">
        {/* Hero */}
        <div className="gradient-hero py-12 md:py-16 relative overflow-hidden">
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div className="absolute top-10 right-20 w-60 h-60 bg-ev-green-500/10 rounded-full blur-3xl" />
          </div>
          <div className="relative max-w-4xl mx-auto px-4 sm:px-6 text-center">
            <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
              EV Travel Blog & Guides
            </h1>
            <p className="text-gray-400 max-w-xl mx-auto">
              Road trip stories, charging guides, vehicle reviews, and tips from the EV community.
            </p>
            <button className="mt-6 inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold gradient-accent text-white shadow-glow hover:shadow-glow-lg transition-all">
              <PenSquare className="w-4 h-4" /> Write a Blog
            </button>
          </div>
        </div>

        {/* Blog Grid */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
          {/* Featured Blog */}
          <div className="card overflow-hidden mb-8 group" id="featured-blog">
            <div className="md:flex">
              <div className="md:w-1/2 h-64 md:h-auto bg-[var(--bg-tertiary)] relative overflow-hidden">
                <img
                  src={sampleBlogs[0].coverImage}
                  alt={sampleBlogs[0].title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <div className="absolute top-3 left-3">
                  <span className="badge bg-[var(--accent)] text-white">Featured</span>
                </div>
              </div>
              <div className="md:w-1/2 p-6 md:p-8 flex flex-col justify-center">
                <div className="flex flex-wrap gap-2 mb-3">
                  {sampleBlogs[0].tags.slice(0, 3).map((tag) => (
                    <span key={tag} className="text-xs font-medium text-[var(--accent)] bg-[var(--accent-light)] px-2 py-0.5 rounded-full">
                      {tag}
                    </span>
                  ))}
                </div>
                <h2 className="text-xl md:text-2xl font-bold text-[var(--text-primary)] group-hover:text-[var(--accent)] transition-colors">
                  <Link href={`/blog/${sampleBlogs[0].slug}`}>{sampleBlogs[0].title}</Link>
                </h2>
                <p className="text-[var(--text-secondary)] mt-2 leading-relaxed text-sm">
                  {sampleBlogs[0].excerpt}
                </p>
                <div className="flex items-center gap-4 mt-4 text-xs text-[var(--text-tertiary)]">
                  <span className="flex items-center gap-1"><User className="w-3 h-3" /> {sampleBlogs[0].author.name}</span>
                  <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {sampleBlogs[0].date}</span>
                  <span className="flex items-center gap-1"><Eye className="w-3 h-3" /> {sampleBlogs[0].views.toLocaleString()}</span>
                  <span className="flex items-center gap-1"><Heart className="w-3 h-3" /> {sampleBlogs[0].likes}</span>
                </div>
                <Link
                  href={`/blog/${sampleBlogs[0].slug}`}
                  className="inline-flex items-center gap-1 mt-4 text-sm font-semibold text-[var(--accent)] hover:underline"
                >
                  Read More <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </div>

          {/* Blog Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sampleBlogs.slice(1).map((blog) => (
              <article key={blog.slug} className="card overflow-hidden group" id={`blog-card-${blog.slug}`}>
                <div className="h-48 bg-[var(--bg-tertiary)] relative overflow-hidden">
                  <img
                    src={blog.coverImage}
                    alt={blog.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                </div>
                <div className="p-5">
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {blog.tags.slice(0, 2).map((tag) => (
                      <span key={tag} className="text-xs font-medium text-[var(--accent)] bg-[var(--accent-light)] px-2 py-0.5 rounded-full">
                        {tag}
                      </span>
                    ))}
                  </div>
                  <h3 className="font-bold text-[var(--text-primary)] group-hover:text-[var(--accent)] transition-colors line-clamp-2">
                    <Link href={`/blog/${blog.slug}`}>{blog.title}</Link>
                  </h3>
                  <p className="text-sm text-[var(--text-secondary)] mt-2 line-clamp-2">
                    {blog.excerpt}
                  </p>
                  <div className="flex items-center justify-between mt-4 pt-3 border-t border-[var(--border-primary)]">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full bg-[var(--accent)] text-white flex items-center justify-center text-xs font-bold">
                        {blog.author.avatar}
                      </div>
                      <span className="text-xs text-[var(--text-secondary)]">{blog.author.name}</span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-[var(--text-tertiary)]">
                      <span>{blog.readTime}</span>
                      <span className="flex items-center gap-0.5"><Heart className="w-3 h-3" /> {blog.likes}</span>
                    </div>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
