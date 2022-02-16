// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getFirestore } from "@firebase/firestore";
import { getDatabase } from "firebase/database";

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyD7YAq4g0z97K_0zWDF05yRO43lZjEc40I",
  authDomain: "tweetstockchat.firebaseapp.com",
  databaseURL:
    "https://tweetstockchat-default-rtdb.europe-west1.firebasedatabase.app",
  projectId: "tweetstockchat",
  storageBucket: "tweetstockchat.appspot.com",
  messagingSenderId: "133578785694",
  appId: "1:133578785694:web:6b8b07afd6c1c3cf834c8f",
  measurementId: "G-6GCWN39XXC",
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

export const FireBaseDB = getFirestore(app);
export const RealTimeDB = getDatabase(app);
