/**
 * AuthContext – Firebase Authentication integration with Flask sync backend support.
 */
import { createContext, useContext, useEffect, useState } from "react";
import { 
  onAuthStateChanged, 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  updateProfile,
  signInWithPopup,
  signOut 
} from "firebase/auth";
import { auth, googleProvider } from "../api/firebase";
import { authApi } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [firebaseUser, setFirebaseUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      setFirebaseUser(currentUser);
      if (currentUser) {
        try {
          const idToken = await currentUser.getIdToken();
          setToken(idToken);
          localStorage.setItem("saferoute_token", idToken);
          
          // Optionally sync with backend or get profile
          try {
            const data = await authApi.me(idToken);
            setUser(data.user);
          } catch {
            setUser({
              id: currentUser.uid,
              name: currentUser.displayName || currentUser.email.split("@")[0],
              email: currentUser.email,
            });
          }
        } catch (err) {
          console.error("Error getting ID token:", err);
          setUser(null);
          setToken(null);
        }
      } else {
        setUser(null);
        setToken(null);
        localStorage.removeItem("saferoute_token");
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  async function register({ name, email, password, phone }) {
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    if (name) {
      await updateProfile(userCredential.user, { displayName: name });
    }
    const idToken = await userCredential.user.getIdToken();
    setToken(idToken);
    localStorage.setItem("saferoute_token", idToken);
    
    // Sync user details to backend/firestore
    try {
      await authApi.sync({ name, email, phone }, idToken);
    } catch (e) {
      console.warn("Backend sync notice:", e);
    }

    const userData = {
      id: userCredential.user.uid,
      name: name || email.split("@")[0],
      email,
      phone
    };
    setUser(userData);
    return userData;
  }

  async function login({ email, password }) {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    const idToken = await userCredential.user.getIdToken();
    setToken(idToken);
    localStorage.setItem("saferoute_token", idToken);

    const userData = {
      id: userCredential.user.uid,
      name: userCredential.user.displayName || email.split("@")[0],
      email
    };
    setUser(userData);
    return userData;
  }

  async function loginWithGoogle() {
    const result = await signInWithPopup(auth, googleProvider);
    const idToken = await result.user.getIdToken();
    setToken(idToken);
    localStorage.setItem("saferoute_token", idToken);

    const userData = {
      id: result.user.uid,
      name: result.user.displayName,
      email: result.user.email
    };
    
    try {
      await authApi.sync({ name: result.user.displayName, email: result.user.email }, idToken);
    } catch (e) {
      console.warn("Google sync notice:", e);
    }

    setUser(userData);
    return userData;
  }

  async function logout() {
    await signOut(auth);
    setUser(null);
    setToken(null);
    localStorage.removeItem("saferoute_token");
  }

  const value = {
    user,
    firebaseUser,
    token,
    loading,
    isAuthenticated: Boolean(firebaseUser),
    register,
    login,
    loginWithGoogle,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return ctx;
}
