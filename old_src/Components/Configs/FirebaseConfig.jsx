// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getFirestore } from "@firebase/firestore";
import { getDatabase, ref } from "firebase/database";

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
// const chatFirebaseConfig = {
//   apiKey: "AIzaSyD7YAq4g0z97K_0zWDF05yRO43lZjEc40I",
//   authDomain: "tweetstockchat.firebaseapp.com",
//   databaseURL:
//     "https://tweetstockchat-default-rtdb.europe-west1.firebasedatabase.app",
//   projectId: "tweetstockchat",
//   storageBucket: "tweetstockchat.appspot.com",
//   messagingSenderId: "133578785694",
//   appId: "1:133578785694:web:6b8b07afd6c1c3cf834c8f",
//   measurementId: "G-6GCWN39XXC",
// };
// (2) Pred DB Initialize Firebase
const FirebaseConfig = {
  apiKey: "AIzaSyAbHDxlP3DTVYvsfS4lrJM6k9NzYaiw0fc",
  authDomain: "tweetstockpred.firebaseapp.com",
  databaseURL:
    "https://tweetstockpred-default-rtdb.europe-west1.firebasedatabase.app",
  projectId: "tweetstockpred",
  storageBucket: "tweetstockpred.appspot.com",
  messagingSenderId: "576775960586",
  appId: "1:576775960586:web:0825f797f3a1ea24ff47f3",
  measurementId: "G-GGKEFFC84S",
};

// (1) Chat DB Initialize Firebase

const app = initializeApp(FirebaseConfig);
const analytics = getAnalytics(app);

export const FireBaseDB = getFirestore(app);
 const RealTimeDB = getDatabase(app);

export const getRealTimeDBRef = (path) => {
  return ref(RealTimeDB, path);
};
