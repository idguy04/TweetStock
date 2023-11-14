import React from "react";
import NewsCard from "./NewsCard";
import "../../../Shared/LoadingCircle";
import LoadingCircle from "../../../Shared/LoadingCircle";

export default function NewsCardsContainer(props) {
  return (
    <div className="newsCardsContainer">
      {props.news ? (
        props.news.map((newsData) => (
          <NewsCard key={newsData.id} newsData={newsData} />
        ))
      ) : (
        <LoadingCircle />
      )}
    </div>
  );
}
