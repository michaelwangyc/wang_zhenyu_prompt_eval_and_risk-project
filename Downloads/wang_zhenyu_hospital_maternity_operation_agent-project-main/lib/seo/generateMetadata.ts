import { Metadata } from "next"
import { SEOConfig } from "@/types"
import { DEFAULT_SEO_CONFIG, COMMON_KEYWORDS } from "./config"

export function generateSEOMetadata(config: SEOConfig): Metadata {
  // 合并默认配置和页面配置
  const mergedConfig = {
    ...DEFAULT_SEO_CONFIG,
    ...config,
    keywords: config.keywords
      ? [...new Set([...COMMON_KEYWORDS, ...config.keywords])]
      : COMMON_KEYWORDS,
  }

  const {
    title,
    description,
    keywords,
    url,
    siteName,
    image,
    imageWidth,
    imageHeight,
    imageAlt,
    author,
    creator,
    ogTitle,
    ogDescription,
    twitterTitle,
    twitterDescription,
    locale,
    type,
    noIndex,
    noFollow,
  } = mergedConfig

  return {
    title,
    description,
    keywords,
    authors: author ? [author] : undefined,
    creator,

    openGraph: {
      title: ogTitle || title,
      description: ogDescription || description,
      url: url || author?.url,
      siteName,
      images: image
        ? [{
            url: image,
            width: imageWidth,
            height: imageHeight,
            alt: imageAlt || title,
          }]
        : undefined,
      locale,
      type,
    },

    twitter: {
      card: "summary_large_image",
      title: twitterTitle || title,
      description: twitterDescription || description,
      images: image ? [image] : undefined,
    },

    robots: {
      index: !noIndex,
      follow: !noFollow,
      googleBot: {
        index: !noIndex,
        follow: !noFollow,
        "max-video-preview": -1,
        "max-image-preview": "large",
        "max-snippet": -1,
      },
    },
  }
}
